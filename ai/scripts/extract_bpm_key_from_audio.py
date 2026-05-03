#!/usr/bin/env python3
"""S3 원본 음원에서 BPM·조성을 librosa로 추정하고, 결과를 출력하거나 songs 테이블에 반영.

Spotify audio-features가 막힌 경우의 대안. 키는 HPSS + CQT/STFT/CENS 융합 +
Krumhansl·Temperley 프로파일 + 긴 곡은 구간별 득표로 추정(완벽하진 않음).
5곡 정도 돌려보고 수동 보정 여부를 결정하면 됨.

기본은 **전체 길이** 로드 후 분석(BPM·키 모두 곡 전체가 더 안정적인 경우가 많음).
빠른 시험만 할 때 `--max-seconds 90` 같이 앞부분만 쓰면 됨.

사용 (ai 디렉터리):
  # 한 곡만 (테스트 추천)
  python scripts/extract_bpm_key_from_audio.py --song-id '<uuid>' --dry-run
  # 여러 곡
  python scripts/extract_bpm_key_from_audio.py --limit 5 --dry-run
  python scripts/extract_bpm_key_from_audio.py --song-id '<uuid>' --apply
  # 키만 Tunebat 등과 맞추고 BPM은 자동:
  python scripts/extract_bpm_key_from_audio.py --song-id '<uuid>' --apply --key-override 'Ab major'
  # BPM만 DB 반영(키는 건드리지 않음):
  python scripts/extract_bpm_key_from_audio.py --song-id '<uuid>' --apply --apply-bpm-only
  # BPM만, 곡 3개 + DB 반영(키 추정 생략으로 더 빠름):
  python scripts/extract_bpm_key_from_audio.py --limit 3 --apply --apply-bpm-only
  python scripts/extract_bpm_key_from_audio.py --song-ids 'uuid1,uuid2,uuid3' --apply --apply-bpm-only

환경: ai/.env — SUPABASE_*, S3_BUCKET_NAME, AWS 자격증명(또는 환경에 이미 설정)
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID

import boto3
import numpy as np

# SciPy 2.x: scipy.signal.hann 제거 → librosa 0.10이 AttributeError. librosa import 전에 보정.
import scipy.signal as _scipy_signal

if not hasattr(_scipy_signal, "hann"):
    from scipy.signal.windows import hann as _hann_window

    _scipy_signal.hann = _hann_window  # type: ignore[attr-defined]

import librosa
from dotenv import load_dotenv
from supabase import create_client

logger = logging.getLogger(__name__)

_AI_ROOT = Path(__file__).resolve().parent.parent
_PITCH = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

# Krumhansl–Schmuckler (장/단)
_KS_MAJOR = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88], dtype=np.float64
)
_KS_MINOR = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17], dtype=np.float64
)
# Temperley (팝/록에 가끔 KS보다 나음)
_TEMP_MAJOR = np.array(
    [5.0, 2.0, 3.5, 2.0, 4.5, 4.0, 2.0, 4.5, 2.0, 3.5, 2.0, 1.5], dtype=np.float64
)
_TEMP_MINOR = np.array(
    [5.0, 2.0, 3.5, 4.5, 2.0, 4.0, 2.0, 4.5, 3.5, 2.0, 1.5, 4.0], dtype=np.float64
)

_CHROMA_HOP = 512


def _load_env() -> None:
    for p in (_AI_ROOT / ".env", _AI_ROOT.parent / ".env"):
        if p.exists():
            load_dotenv(p)
            return
    load_dotenv()


def _supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 필요")
    return create_client(url, key)


def _s3_download(bucket: str, key: str, dest: Path) -> None:
    boto3.client("s3").download_file(bucket, key, str(dest))


def estimate_bpm(audio: np.ndarray, sr: int) -> tuple[float, float]:
    """(bpm, confidence 근사 0~1)"""
    tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
    if isinstance(tempo, (np.ndarray, list)):
        t = np.squeeze(tempo)
        tempo = float(t.flat[0]) if t.size else 0.0
    else:
        tempo = float(tempo)
    if tempo <= 0 or not np.isfinite(tempo):
        return 0.0, 0.0
    if len(beats) > 1:
        bi = np.diff(beats)
        m = float(np.mean(bi))
        conf = float(np.clip(1.0 - (np.std(bi) / m), 0.0, 1.0)) if m > 0 else 0.5
    else:
        conf = 0.5
    return tempo, conf


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    d = float(np.linalg.norm(a) * np.linalg.norm(b))
    if d < 1e-12:
        return 0.0
    return float(np.dot(a, b) / d)


def _fused_chroma_vector(y_harm: np.ndarray, sr: int) -> np.ndarray:
    """CQT + STFT + (가능하면) CENS 크로마를 맞춰 합친 뒤 12차원 분포."""
    cqt = librosa.feature.chroma_cqt(y=y_harm, sr=sr, hop_length=_CHROMA_HOP)
    stft = librosa.feature.chroma_stft(y=y_harm, sr=sr, hop_length=_CHROMA_HOP)
    parts = [cqt, stft]
    try:
        cens = librosa.feature.chroma_cens(y=y_harm, sr=sr, hop_length=_CHROMA_HOP)
        parts.append(cens)
    except Exception:
        pass
    if not parts or min(p.shape[1] for p in parts) < 1:
        return np.ones(12, dtype=np.float64) / 12.0
    t = min(p.shape[1] for p in parts)
    blend = sum(p[:, :t] for p in parts) / float(len(parts))
    v = np.mean(blend, axis=1).astype(np.float64)
    s = float(np.sum(v))
    if s < 1e-12:
        return np.ones(12, dtype=np.float64) / 12.0
    return v / s


def _key_scores_24(v: np.ndarray, maj: np.ndarray, min_: np.ndarray) -> dict[str, float]:
    maj_n = maj / (np.linalg.norm(maj) + 1e-12)
    min_n = min_ / (np.linalg.norm(min_) + 1e-12)
    out: dict[str, float] = {}
    for root in range(12):
        out[f"{_PITCH[root]} major"] = _pearson(v, np.roll(maj_n, root))
        out[f"{_PITCH[root]} minor"] = _pearson(v, np.roll(min_n, root))
    return out


def estimate_key_refined(
    audio: np.ndarray, sr: int
) -> tuple[str, float, list[tuple[str, float]]]:
    """HPSS → 융합 크로마 → KS+Temperley 평균 상관 → 시간 구간별 점수 합산.

    완벽하지 않음(믹스·전조·상대조 혼동). Tunebat 등과 100% 일치 보장 없음.
    """
    y_h, _ = librosa.effects.hpss(audio)
    n = len(y_h)
    if n < sr * 3:
        return "Unknown", 0.0, []

    dur_sec = n / float(sr)
    if dur_sec < 42.0:
        segment_ranges: list[tuple[int, int]] = [(0, n)]
    else:
        n_seg = int(np.clip(round(dur_sec / 28.0), 3, 10))
        chunk = n // n_seg
        segment_ranges = []
        for i in range(n_seg):
            a = i * chunk
            b = n if i == n_seg - 1 else (i + 1) * chunk
            if b - a >= int(sr * 4):
                segment_ranges.append((a, b))

    if not segment_ranges:
        segment_ranges = [(0, n)]

    totals: dict[str, float] = {}
    for a, b in segment_ranges:
        v = _fused_chroma_vector(y_h[a:b], sr)
        ks = _key_scores_24(v, _KS_MAJOR, _KS_MINOR)
        tm = _key_scores_24(v, _TEMP_MAJOR, _TEMP_MINOR)
        for lab in ks:
            sc = 0.5 * ks[lab] + 0.5 * tm.get(lab, 0.0)
            totals[lab] = totals.get(lab, 0.0) + sc

    ranked = sorted(totals.items(), key=lambda x: -x[1])
    best_lab, best_sum = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    n_seg_eff = float(len(segment_ranges))
    margin = (best_sum - second) / n_seg_eff
    conf = float(np.clip(0.5 + 0.5 * margin, 0.0, 1.0))
    top = [(lab, tot / n_seg_eff) for lab, tot in ranked[:5]]
    return best_lab, conf, top


def load_audio(path: Path, max_seconds: float | None) -> tuple[np.ndarray, int]:
    dur = max_seconds if max_seconds and max_seconds > 0 else None
    y, sr = librosa.load(str(path), sr=None, mono=True, duration=dur)
    return y, int(sr)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    _load_env()

    p = argparse.ArgumentParser(description="음원에서 BPM·키 추정 → 콘솔 / songs DB")
    p.add_argument(
        "--song-id",
        type=str,
        default=None,
        help="이 UUID 곡 1곡만 처리 (--song-ids, --limit 과 배타). raw_s3_key 필수.",
    )
    p.add_argument(
        "--song-ids",
        type=str,
        default=None,
        help="쉼표로 구분한 UUID 여러 개 (순서 유지). --song-id / 기본 limit 과 배타.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=5,
        help="--song-id 없을 때만 사용: 처리할 곡 수 (기본 5)",
    )
    p.add_argument(
        "--max-seconds",
        type=float,
        default=0.0,
        help="앞 N초만 분석(빠른 테스트용). 기본 0 = 파일 전체(권장)",
    )
    p.add_argument("--dry-run", action="store_true", help="DB에 쓰지 않고 출력만")
    p.add_argument(
        "--apply",
        action="store_true",
        help="songs 테이블에 bpm, key 컬럼 업데이트 (dry-run과 동시 사용 안 함)",
    )
    p.add_argument(
        "--key-override",
        type=str,
        default=None,
        help="1곡만 처리할 때: DB·요약에 쓸 키 문자열(자동 추정은 참고용으로만 로그). 예: 'Ab major'",
    )
    p.add_argument(
        "--apply-bpm-only",
        action="store_true",
        help="--apply 시 bpm 만 갱신(key 컬럼 미변경). 이 플래그 켜면 키 추정도 생략(더 빠름).",
    )
    args = p.parse_args()

    if args.song_id and args.song_ids:
        logger.error("--song-id 와 --song-ids 는 같이 쓸 수 없습니다.")
        sys.exit(1)

    if args.apply_bpm_only and args.key_override:
        logger.error("--apply-bpm-only 와 --key-override 는 같이 쓰지 마세요.")
        sys.exit(1)

    bucket = (os.getenv("S3_BUCKET_NAME") or "").strip()
    if not bucket:
        logger.error("S3_BUCKET_NAME 이 .env에 필요합니다.")
        sys.exit(1)

    max_sec = None if args.max_seconds <= 0 else args.max_seconds
    supabase = _supabase()

    if args.song_id:
        try:
            UUID(args.song_id)
        except ValueError:
            logger.error("--song-id 는 UUID 형식이어야 합니다.")
            sys.exit(1)
        res = (
            supabase.table("songs")
            .select("id,title,artist,raw_s3_key")
            .eq("id", args.song_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            logger.error("해당 id의 곡이 없습니다.")
            sys.exit(1)
        if not (rows[0].get("raw_s3_key") or "").strip():
            logger.error("이 곡에 raw_s3_key가 없습니다. S3에 올린 뒤 다시 시도하세요.")
            sys.exit(1)
    elif args.song_ids:
        raw_ids = [x.strip() for x in args.song_ids.split(",") if x.strip()]
        if not raw_ids:
            logger.error("--song-ids 가 비었습니다.")
            sys.exit(1)
        for uid in raw_ids:
            try:
                UUID(uid)
            except ValueError:
                logger.error("잘못된 UUID: %s", uid)
                sys.exit(1)
        res = (
            supabase.table("songs")
            .select("id,title,artist,raw_s3_key")
            .in_("id", raw_ids)
            .execute()
        )
        got = {r["id"]: r for r in (res.data or [])}
        rows = []
        for uid in raw_ids:
            r = got.get(uid)
            if not r:
                logger.warning("DB 에 없는 id: %s", uid)
                continue
            if not (r.get("raw_s3_key") or "").strip():
                logger.warning("raw_s3_key 없음, 건너뜀: %s", uid)
                continue
            rows.append(r)
        if not rows:
            logger.error("처리할 곡이 없습니다 (--song-ids 확인).")
            sys.exit(1)
    else:
        res = (
            supabase.table("songs")
            .select("id,title,artist,raw_s3_key")
            .not_.is_("raw_s3_key", "null")
            .neq("raw_s3_key", "")
            .order("created_at", desc=False)
            .limit(args.limit)
            .execute()
        )
        rows = res.data or []
        if not rows:
            logger.error("raw_s3_key 가 있는 곡이 없습니다.")
            sys.exit(1)

    key_override = (args.key_override or "").strip() or None
    if key_override and len(rows) != 1:
        logger.error("--key-override 는 곡 1곡일 때만 사용하세요. --song-id 로 지정하는 것이 가장 안전합니다.")
        sys.exit(1)

    if max_sec:
        logger.info("%d곡 분석 (앞 %.0f초)", len(rows), max_sec)
    else:
        logger.info("%d곡 분석 (전체)", len(rows))

    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="bpm_key_") as tmp:
        tdir = Path(tmp)
        for i, row in enumerate(rows, 1):
            sid = row["id"]
            rkey = row["raw_s3_key"]
            title = row.get("title") or ""
            artist = row.get("artist") or ""
            logger.info("[%d/%d] %s - %s", i, len(rows), artist, title)
            local = tdir / f"{sid}.audio"
            try:
                _s3_download(bucket, rkey, local)
                audio, sr = load_audio(local, max_sec)
                if audio.size == 0:
                    raise RuntimeError("빈 오디오")
                bpm, bconf = estimate_bpm(audio, sr)
                if args.apply_bpm_only:
                    k_auto = "—"
                    kconf = 0.0
                    key_top = []
                    k_final = "—"
                    key_ov = False
                else:
                    k_auto, kconf, key_top = estimate_key_refined(audio, sr)
                    k_final = key_override if key_override else k_auto
                    key_ov = bool(key_override)
                results.append(
                    {
                        "id": sid,
                        "title": title,
                        "artist": artist,
                        "bpm": bpm,
                        "bpm_confidence": bconf,
                        "key": k_final,
                        "key_confidence": kconf,
                        "key_candidates": key_top,
                        "key_auto": k_auto,
                        "key_overridden": key_ov,
                        "bpm_only": bool(args.apply_bpm_only),
                    }
                )
                logger.info(
                    "  → BPM=%.1f (beat_conf~%.2f)%s",
                    bpm,
                    bconf,
                    "  (키 추정 생략: --apply-bpm-only)" if args.apply_bpm_only else "",
                )
                if not args.apply_bpm_only:
                    logger.info(
                        "  → Key=%s%s%s",
                        k_final,
                        f" (자동 score~{kconf:.2f})" if not key_override else " (수동)",
                        "  [key-override]" if key_override else "",
                    )
                    if key_override:
                        logger.info("  자동 추정 참고: %s", k_auto)
                    if key_top:
                        logger.info(
                            "  키 상위 후보 (구간 평균 상관점수, 높을수록 유사): %s",
                            ", ".join(f"{lab} {rr:.3f}" for lab, rr in key_top),
                        )
            except Exception as e:
                logger.exception("  실패: %s", e)
                results.append(
                    {
                        "id": sid,
                        "title": title,
                        "artist": artist,
                        "error": str(e),
                    }
                )

    print("\n======== 요약 ========")
    for r in results:
        if "error" in r:
            print(f"- {r.get('artist')} - {r.get('title')}: ERROR {r['error']}")
        else:
            if r.get("bpm_only"):
                print(
                    f"- {r['artist']} - {r['title']}: "
                    f"BPM={r['bpm']:.1f}  (bpm_conf~{r['bpm_confidence']:.2f})  [키 미계산]"
                )
                continue
            ko = r.get("key_overridden")
            tail = f"  [키 수동]" if ko else ""
            auto_note = ""
            if ko and r.get("key_auto"):
                auto_note = f"    (자동 추정 참고: {r['key_auto']})"
            key_part = (
                f"key~{r['key_confidence']:.2f}"
                if not ko
                else "key 수동"
            )
            print(
                f"- {r['artist']} - {r['title']}: "
                f"BPM={r['bpm']:.1f}  Key={r['key']}  "
                f"(bpm_conf~{r['bpm_confidence']:.2f}, {key_part}){tail}"
            )
            if auto_note:
                print(auto_note)
            cand = r.get("key_candidates") or []
            if cand and not ko:
                line = "    후보: " + ", ".join(f"{lab} ({rr:.3f})" for lab, rr in cand[:5])
                print(line)

    if args.dry_run or not args.apply:
        if not args.apply:
            logger.info("DB 반영 없음. 저장하려면 같은 명령에 --apply 추가.")
        sys.exit(0)

    for r in results:
        if "error" in r or float(r.get("bpm") or 0) <= 0:
            continue
        if args.apply_bpm_only:
            payload: dict[str, Any] = {"bpm": float(r["bpm"])}
        else:
            payload = {"bpm": float(r["bpm"]), "key": r["key"]}
        supabase.table("songs").update(payload).eq("id", r["id"]).execute()
        logger.info("DB 저장: id=%s %s", r["id"], payload)
    logger.info("apply 완료")


if __name__ == "__main__":
    main()

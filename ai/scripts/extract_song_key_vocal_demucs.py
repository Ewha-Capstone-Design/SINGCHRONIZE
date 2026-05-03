#!/usr/bin/env python3
"""S3 원본 → Demucs MR 제거 → 보컬 스템에서 Key 추정 → songs.key 저장 (1곡 테스트용).

이 Key는 **보컬(분리 후) 기반 추정**이며, 상용 메타데이터의 곡 조성과 다를 수 있음.
문서/발표에 명시할 것.

사용 (ai 디렉터리):
  python scripts/extract_song_key_vocal_demucs.py --song-id '<uuid>' --dry-run
  python scripts/extract_song_key_vocal_demucs.py --song-id '<uuid>' --apply

옵션:
  --skip-demucs   MR 제거 생략(원본 믹스로 키만 빠르게 시험, CPU만 있을 때)

환경: SUPABASE_*, S3_BUCKET_NAME, AWS 자격증명, demucs+torch(GPU 권장)
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path
from uuid import UUID

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from extract_bpm_key_from_audio import (  # noqa: E402
    _load_env,
    _s3_download,
    _supabase,
    estimate_key_refined,
)
from vocal_analysis.audio_preprocessing import remove_mr  # noqa: E402

import librosa  # noqa: E402

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    _load_env()

    p = argparse.ArgumentParser(
        description="Demucs 보컬 분리 후 Key 추정 → songs.key",
    )
    p.add_argument("--song-id", type=str, required=True, help="곡 UUID")
    p.add_argument("--dry-run", action="store_true", help="DB 쓰기 생략")
    p.add_argument("--apply", action="store_true", help="songs.key 만 업데이트")
    p.add_argument(
        "--skip-demucs",
        action="store_true",
        help="Demucs 생략(원본 파일로 키 추정만 빠르게 검증)",
    )
    args = p.parse_args()

    try:
        UUID(args.song_id)
    except ValueError:
        logger.error("--song-id 는 UUID 형식이어야 합니다.")
        sys.exit(1)

    bucket = (os.getenv("S3_BUCKET_NAME") or "").strip()
    if not bucket:
        logger.error("S3_BUCKET_NAME 가 .env 에 필요합니다.")
        sys.exit(1)

    supabase = _supabase()
    res = (
        supabase.table("songs")
        .select("id,title,artist,raw_s3_key")
        .eq("id", args.song_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        logger.error("해당 id 의 곡이 없습니다.")
        sys.exit(1)
    row = rows[0]
    rkey = (row.get("raw_s3_key") or "").strip()
    if not rkey:
        logger.error("raw_s3_key 가 없습니다.")
        sys.exit(1)

    title = row.get("title") or ""
    artist = row.get("artist") or ""
    sid = row["id"]
    logger.info("대상: %s | %s - %s", sid, artist, title)

    with tempfile.TemporaryDirectory(prefix="song_key_demucs_") as tmp:
        tdir = Path(tmp)
        local_mix = tdir / "input.audio"
        _s3_download(bucket, rkey, local_mix)

        if args.skip_demucs:
            logger.warning("--skip-demucs: 원본 믹스로 키 추정 (보컬 분리 없음)")
            vocals_path = local_mix
        else:
            voc_dir = tdir / "demucs_out"
            voc_dir.mkdir(parents=True, exist_ok=True)
            out = remove_mr(str(local_mix), output_dir=str(voc_dir))
            out_p = Path(out).resolve()
            if out_p.resolve() == local_mix.resolve():
                logger.error(
                    "Demucs 가 원본 경로를 반환했습니다. "
                    "torch/demucs 설치·GPU 메모리·오디오 포맷을 확인하세요."
                )
                sys.exit(1)
            if not out_p.exists():
                logger.error("보컬 파일이 없습니다: %s", out)
                sys.exit(1)
            vocals_path = out_p

        y, sr = librosa.load(str(vocals_path), sr=None, mono=True)
        if y.size == 0:
            logger.error("빈 오디오입니다.")
            sys.exit(1)

        k_label, k_conf, top = estimate_key_refined(y, int(sr))
        logger.info(
            "Key=%s (내부 score~%.2f) | 소스=%s",
            k_label,
            k_conf,
            "vocal_stem_demucs" if not args.skip_demucs else "full_mix",
        )
        if top:
            logger.info(
                "상위 후보: %s",
                ", ".join(f"{lab} {sc:.3f}" for lab, sc in top),
            )

        print("\n======== 결과 ========")
        print(f"곡: {artist} - {title}")
        print(f"key (DB 반영 값): {k_label}")
        print(f"정의: 보컬 분리 후 크로마 기반 추정 (상용 곡 Key 와 다를 수 있음)")

        if args.dry_run or not args.apply:
            if not args.apply:
                logger.info("DB 반영 없음. 저장: --apply")
            return

        supabase.table("songs").update({"key": k_label}).eq("id", sid).execute()
        logger.info("songs.key 저장 완료: id=%s", sid)


if __name__ == "__main__":
    main()

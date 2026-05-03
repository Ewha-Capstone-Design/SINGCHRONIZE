#!/usr/bin/env python3
"""songs 한 곡을 Spotify로 검색해 BPM·조성을 가져와 Supabase에 저장.

데이터 출처 (순서대로 시도):
  1) GET /v1/audio-features — 간단한 요약 특징
  2) GET /v1/audio-analysis/{{id}} 의 track 객체 — tempo/key/mode 동일 계열
     (문서: https://developer.spotify.com/documentation/web-api/reference/get-audio-analysis )

주의 (403 Forbidden):
  - "위 둘" = audio-features 와 audio-analysis 두 API (Spotify가 2024-11-27 공지에서
    같은 제한 목록에 넣음).
  - 그 제한에 해당하는 앱(예: 그날 이후 새로 만든 앱, Extended 승인 없는 개발 모드 앱)은
    위 두 API를 호출할 때 둘 다 403이 날 수 있음. 검색(search) 등 다른 엔드포인트는 될 수 있음.
  - 그래서 features가 403이면 analysis로 바꿔도 같은 이유로 막히는 경우가 많음.
  https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api

백엔드가 아닌 AI 파이프라인 스크립트로만 둡니다.

사용법 (ai 디렉터리에서):
  python scripts/fetch_spotify_bpm_key.py [--song-id UUID] [--dry-run]
  python scripts/fetch_spotify_bpm_key.py --all-songs [--only-missing-bpm] [--dry-run]

환경 변수 (ai/.env 등):
  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
  SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
  SPOTIFY_ACCESS_TOKEN (선택): 웹/앱에서 발급된 Bearer 토큰. 설정 시 검색·audio-features 등
    모든 Spotify 호출에 이 토큰을 사용합니다(클라이언트 크리덴셜보다 우선).
"""
from __future__ import annotations

import argparse
import base64
import logging
import os
import re
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
from dotenv import load_dotenv
from supabase import create_client

logger = logging.getLogger(__name__)

_PITCH_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

_SCRIPT_DIR = Path(__file__).resolve().parent
_AI_ROOT = _SCRIPT_DIR.parent


def _load_env() -> None:
    for env_path in (_AI_ROOT / ".env", _AI_ROOT.parent / ".env"):
        if env_path.exists():
            load_dotenv(env_path)
            logger.debug("Loaded .env: %s", env_path)
            return
    load_dotenv()


def _get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 가 필요합니다.")
    return create_client(url, key)


def spotify_key_mode_to_label(key: int | None, mode: int | None) -> str | None:
    if key is None or key < 0:
        return None
    root = _PITCH_NAMES[key % 12]
    if mode == 1:
        return f"{root} major"
    if mode == 0:
        return f"{root} minor"
    return root


def _bpm_for_db(tempo: Any) -> int | None:
    """songs.bpm 이 integer 컬럼인 경우 Spotify 실수 tempo 를 반올림해 저장."""
    if tempo is None:
        return None
    try:
        return int(round(float(tempo)))
    except (TypeError, ValueError):
        return None


def _resolve_spotify_token() -> str:
    """SPOTIFY_ACCESS_TOKEN 이 있으면 사용, 없으면 client_credentials 로 발급."""
    env_tok = (os.getenv("SPOTIFY_ACCESS_TOKEN") or "").strip()
    if env_tok:
        return env_tok
    cid = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    sec = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
    if not cid or not sec:
        raise RuntimeError(
            "SPOTIFY_ACCESS_TOKEN 이 없으면 SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET 이 필요합니다."
        )
    return _spotify_token(cid, sec)


def _spotify_token(client_id: str, client_secret: str) -> str:
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    r = httpx.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
        timeout=30.0,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def _spotify_search(
    q: str, token: str, *, market: str | None = "KR", limit: int = 15
) -> dict[str, Any]:
    params: dict[str, Any] = {"q": q, "type": "track", "limit": limit}
    if market:
        params["market"] = market
    max_429 = 8
    for attempt in range(max_429):
        r = httpx.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=30.0,
        )
        if r.status_code == 401:
            raise RuntimeError("Spotify 토큰 만료/거부 — 자격 증명을 확인하세요.")
        if r.status_code == 429:
            wait = 3.0
            ra = r.headers.get("Retry-After")
            if ra:
                try:
                    wait = float(ra) + 1.0
                except ValueError:
                    pass
            wait = min(wait + attempt * 2.0, 90.0)
            logger.warning(
                "Spotify search 429 → %.0fs 대기 후 재시도 (%d/%d)",
                wait,
                attempt + 1,
                max_429,
            )
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Spotify search: 429 반복으로 포기했습니다. 잠시 후 다시 실행하세요.")


_SPOTIFY_API_CHANGES_URL = (
    "https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api"
)


def _log_spotify_analysis_blocked(features_body: str, analysis_body: str) -> None:
    logger.error(
        "Spotify /v1/audio-features 와 /v1/audio-analysis 가 모두 사용 불가(403)입니다.\n"
        "  → 두 엔드포인트는 2024-11-27 Web API 변경에서 같은 제한 목록에 포함됩니다.\n"
        "  → 대안: Extended Web API 문의, 또는 음원 파일 기반 BPM/키 추출.\n"
        "  공지: %s\n"
        "  audio-features 응답 일부: %s\n"
        "  audio-analysis 응답 일부: %s",
        _SPOTIFY_API_CHANGES_URL,
        (features_body or "")[:400] or "(empty)",
        (analysis_body or "")[:400] or "(empty)",
    )


def _tempo_key_mode_from_dict(d: dict[str, Any]) -> tuple[Any, int | None, int | None]:
    tempo = d.get("tempo")
    key_raw = d.get("key")
    mode_raw = d.get("mode")
    kr = key_raw if isinstance(key_raw, int) else None
    mr = mode_raw if isinstance(mode_raw, int) else None
    return tempo, kr, mr


def _fetch_audio_features_by_ids(
    track_ids: list[str], token: str
) -> dict[str, dict[str, Any]]:
    """Spotify track id -> audio_features 객체 (null 제외). 최대 100개씩 요청."""
    out: dict[str, dict[str, Any]] = {}
    unique = list(dict.fromkeys(tid for tid in track_ids if tid))
    for i in range(0, len(unique), 100):
        chunk = unique[i : i + 100]
        r = httpx.get(
            "https://api.spotify.com/v1/audio-features",
            headers={"Authorization": f"Bearer {token}"},
            params={"ids": ",".join(chunk)},
            timeout=30.0,
        )
        if r.status_code == 401:
            raise RuntimeError("Spotify 토큰 만료/거부 — SPOTIFY_ACCESS_TOKEN 또는 자격 증명을 확인하세요.")
        r.raise_for_status()
        for feat in r.json().get("audio_features") or []:
            if isinstance(feat, dict) and feat.get("id"):
                out[str(feat["id"])] = feat
    return out


def _spotify_bpm_key_via_features_or_analysis(track_id: str, token: str) -> tuple[Any, int | None, int | None, str]:
    """audio-features 우선, 실패·비어 있으면 audio-analysis 의 track."""
    features_403_body = ""
    r = httpx.get(
        "https://api.spotify.com/v1/audio-features",
        headers={"Authorization": f"Bearer {token}"},
        params={"ids": track_id},
        timeout=30.0,
    )
    if r.status_code == 200:
        arr = r.json().get("audio_features") or []
        f0 = arr[0] if arr else None
        if isinstance(f0, dict):
            t, k, m = _tempo_key_mode_from_dict(f0)
            if t is not None or (k is not None and k >= 0) or m is not None:
                return t, k, m, "audio-features"
    elif r.status_code == 403:
        features_403_body = r.text or ""
        logger.info(
            "audio-features 403 → audio-analysis 시도 "
            "(공식 문서상 동일 계열 필드: track.tempo, track.key, track.mode)"
        )
    else:
        r.raise_for_status()

    r2 = httpx.get(
        f"https://api.spotify.com/v1/audio-analysis/{track_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=60.0,
    )
    if r2.status_code == 403:
        if r.status_code == 403:
            _log_spotify_analysis_blocked(features_403_body, r2.text or "")
            raise SystemExit(2)
        r2.raise_for_status()
    r2.raise_for_status()
    track = r2.json().get("track")
    if not isinstance(track, dict):
        logger.error("audio-analysis 응답에 track 객체가 없습니다.")
        raise SystemExit(1)
    t, k, m = _tempo_key_mode_from_dict(track)
    return t, k, m, "audio-analysis"


def _sanitize_fragment(s: str) -> str:
    """Spotify field 검색에서 깨뜨리는 따옴표·개행 등 제거."""
    s = (s or "").strip()
    s = re.sub(r'["\n\r]', " ", s)
    s = re.sub(r"[\u0027\u2018\u2019\u02BC`]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _strip_trailing_parentheticals(s: str) -> str:
    """제목 끝의 (OST), （…） 등 괄호 블록을 반복 제거."""
    t = (s or "").strip()
    while True:
        t2 = re.sub(r"\s*[\(（][^)）]{1,120}[)）]\s*$", "", t).strip()
        if t2 == t:
            break
        t = t2
    return t


def _normalize_loose(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[\s·‧・]+", " ", s)
    s = re.sub(r"[^\w\s가-힣ぁ-ゟァ-ヶ一-龯a-z]", "", s)
    return s.strip()


def _score_track_against_row(item: dict[str, Any], title: str, artist: str) -> float:
    tn = _normalize_loose(item.get("name") or "")
    an = _normalize_loose(
        " ".join((x.get("name") or "") for x in (item.get("artists") or []) if x)
    )
    t = _normalize_loose(title)
    ar = _normalize_loose(artist)
    if not t and not ar:
        return 0.0
    cand_spotify = f"{an} {tn}".strip()
    cand_db1 = f"{ar} {t}".strip()
    cand_db2 = f"{t} {ar}".strip()
    s_pair = max(
        SequenceMatcher(None, cand_db1, cand_spotify).ratio(),
        SequenceMatcher(None, cand_db2, cand_spotify).ratio(),
    )
    st = SequenceMatcher(None, t, tn).ratio() if t else 0.0
    sa = SequenceMatcher(None, ar, an).ratio() if ar else 0.0
    if t and ar:
        return max(s_pair, (st + sa) / 2.0)
    return max(st, sa, s_pair)


def _pick_best_track(items: list[dict[str, Any]], title: str, artist: str) -> dict[str, Any]:
    if len(items) == 1:
        return items[0]
    best = items[0]
    best_s = _score_track_against_row(best, title, artist)
    for it in items[1 : min(len(items), 15)]:
        sc = _score_track_against_row(it, title, artist)
        if sc > best_s:
            best, best_s = it, sc
    return best


def _iter_search_queries(title: str, artist: str) -> list[str]:
    """엄격 필드 검색 → 느슨한 키워드 → 괄호 제거 → DB에 가수·제목 순서가 바뀐 경우."""
    t, a = _sanitize_fragment(title), _sanitize_fragment(artist)
    ts = _strip_trailing_parentheticals(t)
    out: list[str] = []

    def add(q: str) -> None:
        q = q.strip()
        if q and q not in out:
            out.append(q)

    if t and a:
        add(f"{t} {a}")
        add(f'track:"{t}" artist:"{a}"')
    if ts and a and ts != t:
        add(f"{ts} {a}")
        add(f'track:"{ts}" artist:"{a}"')
    if t and a and t.casefold() != a.casefold():
        add(f"{a} {t}")
        add(f'track:"{a}" artist:"{t}"')
    if not out:
        add(f"{t} {a}".strip())
    return out


def _resolve_spotify_track_id(title: str, artist: str, token: str) -> dict[str, Any] | None:
    """여러 쿼리·시장(KR / 전역)으로 검색해 가장 그럴듯한 트랙 1개 반환."""
    markets: list[str | None] = ["KR", None]
    for mkt in markets:
        for q in _iter_search_queries(title, artist):
            try:
                data = _spotify_search(q, token, market=mkt)
            except httpx.HTTPStatusError as e:
                code = e.response.status_code
                if code == 400:
                    logger.debug(
                        "Spotify search 400 (다음 쿼리 시도) q≈%s",
                        (q[:100] + "…") if len(q) > 100 else q,
                    )
                    time.sleep(0.15)
                    continue
                if code == 401:
                    raise RuntimeError(
                        "Spotify 토큰 만료/거부 — SPOTIFY_ACCESS_TOKEN 또는 자격 증명을 확인하세요."
                    ) from e
                raise
            items = (data.get("tracks") or {}).get("items") or []
            if not items:
                time.sleep(0.08)
                continue
            chosen = _pick_best_track(items, title, artist)
            time.sleep(0.08)
            return chosen
    return None


def _paginate_songs(supabase: Any, *, only_missing_bpm: bool = False) -> list[dict[str, Any]]:
    """songs 전체 (id, title, artist) 페이지네이션."""
    page_size = 1000
    start = 0
    all_rows: list[dict[str, Any]] = []
    while True:
        end = start + page_size - 1
        q = (
            supabase.table("songs")
            .select("id,title,artist")
            .order("created_at", desc=False)
            .range(start, end)
        )
        if only_missing_bpm:
            q = q.is_("bpm", "null")
        res = q.execute()
        batch = res.data or []
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size
    return all_rows


def _run_all_songs(
    supabase: Any, token: str, dry_run: bool, *, only_missing_bpm: bool
) -> None:
    rows = _paginate_songs(supabase, only_missing_bpm=only_missing_bpm)
    logger.info(
        "대상 곡 수: %d (%s)",
        len(rows),
        "bpm 비어 있음만" if only_missing_bpm else "전체",
    )
    pairs: list[tuple[str, str]] = []
    search_errors = 0
    for idx, row in enumerate(rows):
        sid = row["id"]
        title = row.get("title") or ""
        artist = row.get("artist") or ""
        try:
            chosen = _resolve_spotify_track_id(title, artist, token)
        except Exception as e:
            search_errors += 1
            logger.warning("검색 실패 id=%s: %s", sid, e)
            continue
        if not chosen:
            logger.warning("검색 결과 없음 id=%s | %s - %s", sid, artist, title)
            continue
        tid = chosen["id"]
        pairs.append((sid, tid))
        if (idx + 1) % 50 == 0:
            logger.info("검색 진행 %d/%d", idx + 1, len(rows))

    logger.info("매칭된 Spotify 트랙: %d / 검색 오류: %d", len(pairs), search_errors)
    if not pairs:
        return

    track_ids = [t for _, t in pairs]
    try:
        feat_map = _fetch_audio_features_by_ids(track_ids, token)
    except httpx.HTTPStatusError as e:
        logger.error("audio-features 배치 요청 실패: %s", e)
        sys.exit(2)

    updated = 0
    skipped = 0
    for sid, tid in pairs:
        feat = feat_map.get(tid)
        if not isinstance(feat, dict):
            logger.warning("audio-features 없음 song_id=%s track_id=%s", sid, tid)
            skipped += 1
            continue
        tempo, key_raw, mode_raw = _tempo_key_mode_from_dict(feat)
        label = spotify_key_mode_to_label(key_raw, mode_raw)
        if tempo is None and label is None:
            logger.warning("tempo/key 모두 없음 song_id=%s track_id=%s", sid, tid)
            skipped += 1
            continue
        if dry_run:
            logger.info(
                "dry-run 저장 생략 id=%s | tempo=%s key=%s",
                sid,
                tempo,
                label,
            )
            updated += 1
            continue
        payload: dict[str, Any] = {}
        if label is not None:
            payload["key"] = label
        bpm_i = _bpm_for_db(tempo)
        if bpm_i is not None:
            payload["bpm"] = bpm_i
        if not payload:
            skipped += 1
            continue
        try:
            supabase.table("songs").update(payload).eq("id", sid).execute()
        except Exception as e:
            logger.error("DB 저장 실패 id=%s: %s", sid, e)
            skipped += 1
            continue
        updated += 1
    logger.info("완료: 저장(또는 dry-run 대상)=%d 건너뜀=%d", updated, skipped)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    _load_env()

    parser = argparse.ArgumentParser(description="Spotify BPM/KEY → songs (Supabase)")
    parser.add_argument("--song-id", type=str, default=None)
    parser.add_argument(
        "--all-songs",
        action="store_true",
        help="songs 테이블의 모든 행에 대해 검색 후 audio-features 배치로 BPM·KEY 저장",
    )
    parser.add_argument(
        "--only-missing-bpm",
        action="store_true",
        help="--all-songs 와 함께: bpm 이 NULL 인 행만 처리 (이미 채워진 곡은 스킵)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.song_id and args.all_songs:
        logger.error("--song-id 와 --all-songs 는 함께 쓸 수 없습니다.")
        sys.exit(1)
    if args.only_missing_bpm and not args.all_songs:
        logger.error("--only-missing-bpm 은 --all-songs 와 함께만 사용할 수 있습니다.")
        sys.exit(1)

    try:
        token = _resolve_spotify_token()
    except RuntimeError as e:
        logger.error("%s", e)
        sys.exit(1)

    supabase = _get_supabase()

    if args.all_songs:
        _run_all_songs(
            supabase, token, args.dry_run, only_missing_bpm=args.only_missing_bpm
        )
        return

    cid = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    sec = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
    if not (os.getenv("SPOTIFY_ACCESS_TOKEN") or "").strip():
        if not cid or not sec:
            logger.error(
                "SPOTIFY_ACCESS_TOKEN 이 없으면 SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET 이 필요합니다."
            )
            sys.exit(1)

    row: dict[str, Any] | None = None
    if args.song_id:
        try:
            UUID(args.song_id)
        except ValueError:
            logger.error("잘못된 --song-id")
            sys.exit(1)
        res = (
            supabase.table("songs")
            .select("id,title,artist,bpm")
            .eq("id", args.song_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            logger.error("해당 id의 곡이 없습니다.")
            sys.exit(1)
        row = rows[0]
    else:
        res = (
            supabase.table("songs")
            .select("id,title,artist,bpm")
            .is_("bpm", "null")
            .order("created_at", desc=False)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            res = (
                supabase.table("songs")
                .select("id,title,artist,bpm")
                .order("created_at", desc=False)
                .limit(1)
                .execute()
            )
            rows = res.data or []
        if not rows:
            logger.error("songs 테이블에 행이 없습니다.")
            sys.exit(1)
        row = rows[0]

    assert row is not None
    title = row.get("title") or ""
    artist = row.get("artist") or ""
    sid = row["id"]
    logger.info("대상: id=%s | %s - %s", sid, artist, title)

    chosen = _resolve_spotify_track_id(title, artist, token)
    if not chosen:
        logger.error("검색 결과 없음 (여러 쿼리·시장 조합 시도함)")
        sys.exit(1)

    tid = chosen["id"]
    sp_name = chosen.get("name") or ""
    sp_art = (chosen.get("artists") or [{}])[0].get("name") or ""
    logger.info("선택 트랙: %s - %s (%s)", sp_art, sp_name, tid)

    tempo, key_raw, mode_raw, src = _spotify_bpm_key_via_features_or_analysis(tid, token)
    label = spotify_key_mode_to_label(key_raw, mode_raw)
    logger.info(
        "출처=%s | tempo=%s key=%s mode=%s → %s",
        src,
        tempo,
        key_raw,
        mode_raw,
        label,
    )

    if args.dry_run:
        logger.info("dry-run: DB 저장 생략")
        return

    payload: dict[str, Any] = {"key": label}
    bpm_i = _bpm_for_db(tempo)
    if bpm_i is not None:
        payload["bpm"] = bpm_i

    supabase.table("songs").update(payload).eq("id", sid).execute()
    logger.info("저장 완료: bpm=%s key=%s", payload.get("bpm"), label)


if __name__ == "__main__":
    main()

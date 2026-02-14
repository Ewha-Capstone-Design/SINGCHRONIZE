import os
import re
import time
import argparse
import tempfile
from pathlib import Path

import boto3
import yt_dlp
from dotenv import load_dotenv
from supabase import create_client, Client
from googleapiclient.discovery import build


# =========================
# ENV
# =========================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

S3_BUCKET = os.getenv("S3_BUCKET_NAME")
S3_PREFIX = (os.getenv("S3_PREFIX") or "raw/youtube").strip().strip("/")

MAX_JOBS = int(os.getenv("MAX_JOBS") or "20")


# =========================
# Helpers
# =========================
def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 가 .env에 필요합니다.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def sanitize_filename(name: str) -> str:
    name = name or "untitled"
    name = re.sub(r"[\\/:*?\"<>|]+", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:160]


def parse_iso8601_duration_to_seconds(duration: str) -> int:
    # 예: PT3M12S, PT1H2M, PT59S
    h = m = s = 0
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if match:
        h = int(match.group(1) or 0)
        m = int(match.group(2) or 0)
        s = int(match.group(3) or 0)
    return h * 3600 + m * 60 + s


def is_pop_genre(genre: str) -> bool:
    """장르에 POP이 포함되어 있는지 확인 (대소문자 무시)"""
    if not genre:
        return False
    return "pop" in genre.lower()


def youtube_search_candidates(title: str, artist: str, genre: str = "") -> list:
    """
    - 가사/lyrics 쿼리로 먼저 유도
    - 결과 여러 개 중에서 Shorts(<=60초) 제외 + cover/live/karaoke 등 감점
    - 여러 후보 URL을 점수순으로 정렬하여 리스트로 반환
    """
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    # 특정 곡은 "가사 해석"으로 검색 (지역 제한 우회)
    title_lower = title.lower()
    if "into the unknown" in title_lower:
        queries = [
            f"{title} {artist} 가사 해석",
            f"{title} 가사 해석",
            f"{title} {artist} lyrics",
        ]
    # 장르에 POP이 있으면 팝송으로 판단
    elif is_pop_genre(genre):
        # 팝송: lyrics video 우선 (비공식 영상이 지역 제한 없는 경우가 많음)
        queries = [
            f"{title} {artist} lyrics video",
            f"{title} {artist} lyrics",
            f"{title} {artist} audio",
        ]
    else:
        # 한국 노래: 가사 우선
        queries = [
            f"{title} {artist} 가사",
            f"{title} {artist} lyrics",
            f"{title} {artist}",
        ]

    all_scored = []
    seen_ids = set()
    last_err = None

    for q in queries:
        try:
            search = youtube.search().list(
                part="id",
                q=q,
                type="video",
                maxResults=5,
                safeSearch="none",
            ).execute()

            items = search.get("items", [])
            if not items:
                continue

            video_ids = [it["id"]["videoId"] for it in items if it.get("id", {}).get("videoId")]
            # 이미 본 ID 제외
            video_ids = [vid for vid in video_ids if vid not in seen_ids]
            if not video_ids:
                continue
            
            for vid in video_ids:
                seen_ids.add(vid)

            # 후보들의 길이/제목 확인 (Shorts 방지)
            detail = youtube.videos().list(
                part="contentDetails,snippet",
                id=",".join(video_ids),
            ).execute()

            for v in detail.get("items", []):
                vid = v["id"]
                vtitle = (v.get("snippet", {}).get("title") or "").lower()
                duration = v.get("contentDetails", {}).get("duration") or "PT0S"
                sec = parse_iso8601_duration_to_seconds(duration)

                score = 0

                # Shorts/너무 짧은 영상 강하게 제외
                if sec <= 60:
                    score -= 100

                # 커버/라이브/노래방 등은 후순위
                bad_words = ["cover", "live", "karaoke", "instrumental", "mr", "reaction", "shorts"]
                if any(w in vtitle for w in bad_words):
                    score -= 10
                
                # lyrics video 가점 (비공식 가사 영상은 지역 제한 적음)
                if "lyrics" in vtitle or "lyric" in vtitle:
                    score += 5

                # 어느 정도 길이가 있으면 가점
                if sec >= 120:
                    score += 3

                all_scored.append((score, vid))

        except Exception as e:
            last_err = e
            # 첫 번째 쿼리 실패 시 바로 에러 던지기 (API 할당량 등)
            if not all_scored:
                raise RuntimeError(f"YouTube 검색 실패: {e}")

    if not all_scored:
        raise RuntimeError(f"YouTube 검색 실패: {last_err}")

    # 점수순 정렬 후 URL 리스트 반환
    all_scored.sort(reverse=True, key=lambda x: x[0])
    return [f"https://www.youtube.com/watch?v={vid}" for _, vid in all_scored]


def youtube_search_best_url(title: str, artist: str, genre: str = "") -> str:
    """하위 호환용: 첫 번째 후보만 반환"""
    candidates = youtube_search_candidates(title, artist, genre)
    return candidates[0] if candidates else None


def download_with_ytdlp(youtube_url: str, output_path: Path, filename: str) -> Path:
    """yt-dlp를 사용하여 영상 다운로드"""
    output_template = str(output_path / filename)
    
    ydl_opts = {
        # H.264(avc1) 코덱 우선 (호환성 좋음), AV1/VP9 회피
        'format': 'bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'merge_output_format': 'mp4',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        video_id = info.get('id', 'unknown')
        
    # 실제 저장된 파일 경로 반환
    return output_path / filename, video_id


def s3_upload(local_path: Path, bucket: str, key: str):
    s3 = boto3.client("s3")
    s3.upload_file(str(local_path), bucket, key)


# =========================
# Supabase DB ops
# =========================
def fetch_new_songs(supabase: Client, limit: int):
    # youtube_url이 이미 있으면 재검색 스킵 가능하도록 같이 읽음
    # NEW와 FAILED 상태 모두 처리
    # download_status도 함께 가져와서 FAILED면 URL 재검색하도록
    res = (
        supabase.table("songs")
        .select("id,title,artist,youtube_url,genre,download_status")
        .in_("download_status", ["NEW", "FAILED"])
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return res.data or []


def update_song(supabase: Client, song_id: str, payload: dict):
    supabase.table("songs").update(payload).eq("id", song_id).execute()


# =========================
# Core batch
# =========================
def process_batch(supabase: Client, limit: int) -> int:
    songs = fetch_new_songs(supabase, limit)
    if not songs:
        return 0

    tmpdir = Path(tempfile.mkdtemp(prefix="yt_dl_"))

    try:
        for s in songs:
            song_id = s["id"]
            title = (s.get("title") or "").strip()
            artist = (s.get("artist") or "").strip()
            youtube_url = (s.get("youtube_url") or "").strip()
            genre = (s.get("genre") or "").strip()
            prev_status = (s.get("download_status") or "").strip()

            if not title or not artist:
                update_song(supabase, song_id, {"download_status": "FAILED"})
                print(f"[FAILED] id={song_id} (title/artist 비어있음)")
                continue

            try:
                # 1) 상태 RUNNING
                update_song(supabase, song_id, {"download_status": "RUNNING"})

                # 2) youtube_url 없거나 FAILED였던 곡은 URL 재검색
                #    (FAILED는 잘못된 URL일 수 있으므로 다시 검색)
                if not youtube_url or prev_status == "FAILED":
                    candidates = youtube_search_candidates(title, artist, genre)
                else:
                    # 기존 URL만 시도
                    candidates = [youtube_url]

                # 3) 다운로드 (여러 후보 순차 시도)
                download_success = False
                last_download_err = None
                
                for candidate_url in candidates:
                    try:
                        video_id_match = re.search(r'v=([a-zA-Z0-9_-]+)', candidate_url)
                        video_id = video_id_match.group(1) if video_id_match else "unknown"
                        
                        filename = f"{song_id}_{sanitize_filename(title)}_{sanitize_filename(artist)}_{video_id}.mp4"
                        local_path, _ = download_with_ytdlp(candidate_url, tmpdir, filename)
                        
                        # 성공 시 URL 업데이트
                        youtube_url = candidate_url
                        download_success = True
                        break
                    except Exception as dl_err:
                        last_download_err = dl_err
                        # 다음 후보로 시도
                        continue
                
                if not download_success:
                    raise RuntimeError(f"모든 후보 다운로드 실패: {last_download_err}")

                # URL 저장 (성공한 URL로)
                update_song(supabase, song_id, {"youtube_url": youtube_url})

                # 4) S3 업로드
                s3_key = f"{S3_PREFIX}/{filename}"
                s3_upload(local_path, S3_BUCKET, s3_key)

                # 5) 로컬 삭제
                local_path.unlink(missing_ok=True)

                # 6) DB 업데이트: raw_s3_key + DONE
                update_song(
                    supabase,
                    song_id,
                    {
                        "raw_s3_key": s3_key,
                        "download_status": "DONE",
                    },
                )

                print(f"[DONE] {title} - {artist} -> s3://{S3_BUCKET}/{s3_key}")

            except Exception as e:
                update_song(supabase, song_id, {"download_status": "FAILED"})
                print(f"[FAILED] {title} - {artist} err={e}")

    finally:
        # tmpdir 비어있으면 삭제
        try:
            tmpdir.rmdir()
        except OSError:
            pass

    return len(songs)


def main():
    # 필수 체크
    if not YOUTUBE_API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY가 없습니다(.env 확인)")
    if not S3_BUCKET:
        raise RuntimeError("S3_BUCKET_NAME이 없습니다(.env 확인)")
    if not (SUPABASE_URL and SUPABASE_KEY):
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY가 없습니다(.env 확인)")

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=MAX_JOBS, help="한 번에 처리할 곡 수")
    parser.add_argument("--loop", action="store_true", help="NEW가 없어질 때까지 반복 실행")
    parser.add_argument("--sleep", type=int, default=3, help="loop 모드에서 배치 간 대기(초)")
    args = parser.parse_args()

    supabase = get_supabase_client()

    if not args.loop:
        n = process_batch(supabase, args.limit)
        print(f"처리 완료: {n}곡")
        return

    total = 0
    while True:
        n = process_batch(supabase, args.limit)
        total += n
        print(f"이번 배치: {n}곡 / 누적 처리 시도: {total}곡")

        if n == 0:
            print("NEW가 없어져서 종료합니다.")
            break

        time.sleep(args.sleep)


if __name__ == "__main__":
    main()

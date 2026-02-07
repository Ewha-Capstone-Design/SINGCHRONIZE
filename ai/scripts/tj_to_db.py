"""
TJ 크롤링 데이터를 Supabase DB에 저장하는 스크립트
- 기존 곡이 있으면: 장르만 누적 업데이트
- 새 곡이면: insert
"""
import os
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# .env 파일 로드
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# TJ API 설정
API_URL = "https://www.tjmedia.com/legacy/api/topAndHot100"

# 장르 순서 (일관된 정렬용)
GENRE_ORDER = ["전체", "POP", "JPOP", "발라드", "댄스", "트로트", "락/메탈", "R&B/어반"]

STR_TYPE_TO_GENRE = {
    "0": "전체",
    "2": "POP",
    "3": "JPOP",
    "4": "발라드",
    "5": "댄스",
    "6": "트로트",
    "9": "락/메탈",
    "11": "R&B/어반",
}


def get_supabase_client() -> Client:
    """Supabase 클라이언트 생성"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY가 .env에 필요합니다")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_tj_top100(str_type: str, start_date: str, end_date: str) -> list[dict]:
    """TJ 미디어에서 인기곡 100을 가져옴"""
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://www.tjmedia.com",
        "Referer": "https://www.tjmedia.com/",
    }
    data = {
        "chartType": "TOP",
        "searchStartDate": start_date,
        "searchEndDate": end_date,
        "strType": str_type,
    }

    r = requests.post(API_URL, headers=headers, data=data, timeout=30)
    r.raise_for_status()
    j = r.json()

    if j.get("resultCode") != "99":
        raise RuntimeError(f"resultCode={j.get('resultCode')} msg={j.get('resultMsg')}")

    return j["resultData"]["items"]


def merge_genre(existing: str | None, new_one: str) -> str:
    """
    기존 장르 문자열에 새 장르를 추가 (중복 방지, 순서 유지)
    예: "발라드,댄스" + "POP" -> "POP,발라드,댄스"
    """
    genres = set()
    
    # 기존 장르 파싱
    if existing:
        for g in str(existing).split(","):
            g = g.strip()
            if g:
                genres.add(g)
    
    # 새 장르 추가
    if new_one:
        genres.add(new_one)
    
    # GENRE_ORDER 순서대로 정렬해서 반환
    return ",".join([g for g in GENRE_ORDER if g in genres])


def save_to_db(supabase: Client, items: list[dict], genre_label: str):
    """
    TJ API 결과를 DB에 저장
    - 기존 곡(title+artist 동일): 장르만 누적 업데이트
    - 새 곡: insert
    
    Args:
        supabase: Supabase 클라이언트
        items: TJ API에서 받은 곡 목록
        genre_label: 저장할 장르 라벨 (예: "발라드", "댄스")
    """
    inserted = 0
    updated = 0
    skipped = 0

    for item in items:
        # TJ API 필드명 주의: indexTitle=가수, indexSong=곡제목
        title = item.get("indexSong", "").strip()
        artist = item.get("indexTitle", "").strip()
        cover = item.get("imgthumb_path", "")

        if not title or not artist:
            skipped += 1
            continue

        # 1) 기존 곡 조회
        res = (supabase.table("songs")
               .select("id, genre")
               .eq("title", title)
               .eq("artist", artist)
               .execute())
        
        existing = res.data[0] if res.data else None

        if not existing:
            # 2) 새 곡 insert
            supabase.table("songs").insert({
                "title": title,
                "artist": artist,
                "album_cover": cover,
                "genre": genre_label,
            }).execute()
            inserted += 1
        else:
            # 3) 기존 곡 update (장르 누적)
            merged = merge_genre(existing.get("genre"), genre_label)
            supabase.table("songs").update({
                "genre": merged,
                "album_cover": cover,  # 커버 이미지도 최신으로 갱신
            }).eq("id", existing["id"]).execute()
            updated += 1

    print(f"저장 완료: inserted={inserted}, updated={updated}, skipped={skipped}")
    return {"inserted": inserted, "updated": updated, "skipped": skipped}


def crawl_and_save(supabase: Client, str_type: str, start_date: str, end_date: str):
    """
    특정 장르의 TJ TOP 100을 크롤링해서 DB에 저장
    """
    genre_label = STR_TYPE_TO_GENRE.get(str_type, "전체")
    print(f"\n[{genre_label}] 크롤링 중... (strType={str_type})")
    
    items = fetch_tj_top100(str_type=str_type, start_date=start_date, end_date=end_date)
    print(f"  크롤링 결과: {len(items)}곡")
    
    return save_to_db(supabase, items, genre_label)


def main():
    """메인 실행"""
    # Supabase 연결
    supabase = get_supabase_client()
    print("Supabase 연결 성공!")
    
    # 날짜 범위 설정
    start_date = "2026-02-01"
    end_date = "2026-02-07"
    
    print(f"\n기간: {start_date} ~ {end_date}")
    

    for str_type in ["0", "2", "4", "5", "6", "11"]:
         crawl_and_save(supabase, str_type, start_date, end_date)


def test_preview():
    """DB 저장 없이 미리보기만"""
    start_date = "2026-02-01"
    end_date = "2026-02-07"
    
    print(f"기간: {start_date} ~ {end_date}")
    print("\n크롤링 미리보기")
    
    items = fetch_tj_top100(str_type="", start_date=start_date, end_date=end_date)
    print(f"총 {len(items)}곡")
    
    print("\n[처음 10개 미리보기]")
    for i, item in enumerate(items[:10], 1):
        title = item.get("indexSong", "")
        artist = item.get("indexTitle", "")
        print(f"  {i:2d}. {artist} - {title}")


if __name__ == "__main__":
    # 테스트용: 미리보기만
    # test_preview()
    
    # 실제 실행: DB에 저장
    main()

import os
from dotenv import load_dotenv
import boto3
from supabase import create_client
from collections import defaultdict

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

S3_BUCKET = os.getenv("S3_BUCKET_NAME")
S3_PREFIX = (os.getenv("S3_PREFIX") or "raw/youtube").strip().strip("/") + "/"

def get_all_s3_keys(bucket: str, prefix: str) -> set[str]:
    s3 = boto3.client("s3")
    keys = set()
    token = None
    while True:
        kwargs = dict(Bucket=bucket, Prefix=prefix, MaxKeys=1000)
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []):
            keys.add(obj["Key"])
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
        else:
            break
    return keys

def get_all_db_rows() -> list[dict]:
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Supabase는 한번에 전량 select가 제한/페이지 필요할 수 있어서 range로 가져옴
    rows = []
    start = 0
    step = 1000

    while True:
        res = (
            sb.table("songs")
            .select("id,title,artist,raw_s3_key,download_status")
            .range(start, start + step - 1)
            .execute()
        )
        batch = res.data or []
        rows.extend(batch)
        if len(batch) < step:
            break
        start += step

    return rows

def main():
    if not (SUPABASE_URL and SUPABASE_KEY):
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 필요")
    if not S3_BUCKET:
        raise RuntimeError("S3_BUCKET_NAME 필요")

    print(f"[INFO] S3 bucket={S3_BUCKET} prefix={S3_PREFIX}")
    s3_keys = get_all_s3_keys(S3_BUCKET, S3_PREFIX)
    print(f"[INFO] S3 objects under prefix: {len(s3_keys)}")

    db_rows = get_all_db_rows()
    print(f"[INFO] DB rows in songs: {len(db_rows)}")

    # DB에서 raw_s3_key 있는 것만 모음
    db_keys = set()
    db_id_by_key = {}
    db_missing_key_rows = []

    for r in db_rows:
        key = (r.get("raw_s3_key") or "").strip()
        if key:
            db_keys.add(key)
            db_id_by_key[key] = r.get("id")
        else:
            db_missing_key_rows.append(r)

    # 1) S3엔 있는데 DB raw_s3_key에 없는 key (S3 orphan)
    s3_only = sorted(list(s3_keys - db_keys))

    # 2) DB엔 있는데 S3에 없는 key (DB stale/missing object)
    db_only = sorted(list(db_keys - s3_keys))

    # 3) DB엔 있는데 raw_s3_key가 없는 곡
    db_missing_key = db_missing_key_rows

    print("\n=== 결과 요약 ===")
    print(f"DB에 raw_s3_key 없는 곡: {len(db_missing_key)}")
    print(f"S3엔 있는데 DB에 없는 key (S3 orphan): {len(s3_only)}")
    print(f"DB엔 있는데 S3에 없는 key (missing in S3): {len(db_only)}")

    # 파일로 저장 (너무 길 수 있어서)
    def write_list(path, items):
        with open(path, "w", encoding="utf-8") as f:
            for x in items:
                f.write(str(x) + "\n")

    write_list("s3_only_keys.txt", s3_only)
    write_list("db_only_keys.txt", db_only)

    with open("db_missing_raw_s3_key.txt", "w", encoding="utf-8") as f:
        for r in db_missing_key:
            f.write(f"{r.get('id')}\t{r.get('download_status')}\t{r.get('title')}\t{r.get('artist')}\n")

    print("\n[FILES]")
    print("- s3_only_keys.txt          : S3엔 있지만 DB raw_s3_key에 없는 객체들")
    print("- db_only_keys.txt          : DB raw_s3_key엔 있지만 S3에 없는 객체들")
    print("- db_missing_raw_s3_key.txt : DB에 있지만 raw_s3_key가 비어있는 곡들")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""로컬 MongoDB에 basescores 형식 문서 1건 저장 후 조회·삭제로 검증."""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

_ai_root = Path(__file__).resolve().parent.parent.parent
try:
    from dotenv import load_dotenv

    load_dotenv(_ai_root / ".env")
except ImportError:
    pass

MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "singchronize")
TEST_JOB_ID = "__local_mongo_save_test__"


def main() -> int:
    try:
        from pymongo import MongoClient
    except ImportError:
        print("pymongo 없음: pip install pymongo", file=sys.stderr)
        return 1

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")

    db = client[MONGO_DB_NAME]
    coll = db["basescores"]

    try:
        coll.delete_many({"job_id": TEST_JOB_ID})
    except Exception as e:
        err = str(e).lower()
        if "authentication" in err or "unauthorized" in err or getattr(e, "code", None) == 13:
            print(
                "MongoDB 쓰기가 거부되었습니다(인증 필요).\n"
                "  • Docker를 root 계정으로 띄웠다면 .env 예:\n"
                "    MONGO_URI=mongodb://USER:PASSWORD@127.0.0.1:27017/?authSource=admin\n"
                "  • 인증 없이 로컬만 쓰려면 컨테이너를 MONGO_INITDB_* 없이 다시 띄우거나,\n"
                "    ai/docker-compose.mongo.yml 로 기동하세요.\n"
                "  • .env 의 MONGO_URI 가 Atlas/원격이면 해당 클러스터용 URI 인지 확인하세요.",
                file=sys.stderr,
            )
        raise

    doc = {
        "job_id": TEST_JOB_ID,
        "user_id": "test-user",
        "song_id": "test-song-1",
        "basescore": 0.99,
        "date": datetime.now().isoformat(),
        "genre": ["가요"],
        "situations": ["친구랑 놀 때"],
        "keywords": ["테스트"],
        "title": "로컬 저장 검증",
        "artist": "script",
        "ecapa_score": 0.0,
        "pitch_total": 0.0,
        "timbre_score": 0.0,
        "created_at": datetime.now(),
    }
    ins = coll.insert_one(doc)
    found = coll.find_one({"_id": ins.inserted_id})

    print(f"URI: {MONGO_URI.split('@')[-1] if '@' in MONGO_URI else MONGO_URI}")
    print(f"DB: {MONGO_DB_NAME}  collection: basescores")
    print(f"inserted_id: {ins.inserted_id}")
    print(f"read back song_id={found.get('song_id')} basescore={found.get('basescore')}")

    coll.delete_many({"job_id": TEST_JOB_ID})
    print("테스트 문서 삭제 완료 (컬렉션은 그대로 유지)")
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

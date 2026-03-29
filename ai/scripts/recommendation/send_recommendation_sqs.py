#!/usr/bin/env python3
"""추천 큐(SQS)에 1차용 메시지 1건 발행. 로컬 워커가 수신해 Mongo에 저장하는 흐름 검증용."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_ai_root = Path(__file__).resolve().parent.parent.parent
try:
    from dotenv import load_dotenv

    load_dotenv(_ai_root / ".env")
except ImportError:
    pass

import boto3


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--job-id", required=True, help="recommendation_logs.id 와 동일한 UUID")
    p.add_argument("--user-id", required=True, help="user_vocal_profiles 가 채워진 유저")
    p.add_argument(
        "--stage",
        default="stage1",
        choices=["stage1", "stage2"],
        help="1차만 Mongo 저장 검증이면 stage1",
    )
    p.add_argument("--s3-key", default="", help="FIRST_REC_FORCE_PIPELINE=1 일 때만 필요")
    p.add_argument(
        "--queue-url",
        default=os.getenv("SQS_QUEUE_URL", ""),
        help="기본: 환경변수 SQS_QUEUE_URL",
    )
    args = p.parse_args()
    if not args.queue_url.strip():
        print("SQS_QUEUE_URL 이 없습니다. ai/.env 또는 --queue-url 를 설정하세요.", file=sys.stderr)
        return 1

    body: dict = {"job_id": args.job_id, "user_id": args.user_id}
    if args.stage:
        body["stage"] = args.stage
    sk = (args.s3_key or "").strip()
    if sk:
        body["s3_key"] = sk

    sqs = boto3.client("sqs")
    r = sqs.send_message(
        QueueUrl=args.queue_url.strip(),
        MessageBody=json.dumps(body, ensure_ascii=False),
    )
    print("SendMessage OK")
    print("  MessageId:", r.get("MessageId"))
    print("  Body:", json.dumps(body, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

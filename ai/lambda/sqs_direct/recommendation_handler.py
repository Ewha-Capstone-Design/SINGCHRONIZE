"""
SQS → 추천 처리 (Lambda 컨테이너).
런타임: 이미지에 scripts/recommendation, scoring_runner, vocal_analysis 일부 포함.
핸들러(이미지 CMD): recommendation.handler
"""
from __future__ import annotations

import json
import os
import sys
import traceback

_task = os.environ.get("LAMBDA_TASK_ROOT", "/var/task")
_scripts_rec = os.path.join(_task, "scripts", "recommendation")
if _scripts_rec not in sys.path:
    sys.path.insert(0, _scripts_rec)

from first_recommendation_worker import get_supabase_client  # noqa: E402
from recommendation_worker import (  # noqa: E402
    fetch_recommendation_user_id,
    process_recommendation_job,
)


def _parse_body(raw: str) -> dict:
    body = json.loads(raw)
    if isinstance(body.get("Message"), str):
        body = json.loads(body["Message"])
    return body


def handler(event, context):
    batch_failures = []
    for record in event.get("Records", []):
        mid = record.get("messageId") or ""
        try:
            body = _parse_body(record["body"])
            job_id = body.get("job_id") or body.get("id")
            if not job_id:
                raise ValueError("SQS body missing job_id")

            supabase = get_supabase_client()
            user_id = fetch_recommendation_user_id(supabase, str(job_id))
            if not user_id:
                raise RuntimeError(
                    f"recommendation_logs 에서 user_id 를 찾을 수 없습니다 (id={job_id})."
                )

            stage_raw = (body.get("stage") or "").strip().lower()
            stage = None
            if stage_raw:
                if stage_raw not in ("stage1", "stage2"):
                    raise ValueError(f"RECOMMENDATION_STAGE 는 stage1 또는 stage2: {stage_raw!r}")
                stage = stage_raw

            s3_key = (body.get("s3_key") or body.get("audio_s3_key") or "").strip()

            process_recommendation_job(str(job_id), user_id, s3_key, stage)
        except Exception:
            traceback.print_exc()
            batch_failures.append({"itemIdentifier": mid})
    return {"batchItemFailures": batch_failures}

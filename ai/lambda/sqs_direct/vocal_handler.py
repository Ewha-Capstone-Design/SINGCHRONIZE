"""
SQS → 보컬 분석 (Lambda 컨테이너).
런타임: 이미지에 scripts/vocal_analysis 전체 + requirements.txt.
핸들러(이미지 CMD): vocal.handler
"""
from __future__ import annotations

import json
import os
import sys
import traceback

_task = os.environ.get("LAMBDA_TASK_ROOT", "/var/task")
_scripts_va = os.path.join(_task, "scripts", "vocal_analysis")
if _scripts_va not in sys.path:
    sys.path.insert(0, _scripts_va)

_worker = None


def _get_worker():
    global _worker
    if _worker is None:
        from vocal_analysis_worker import VocalAnalysisWorker  # noqa: E402

        _worker = VocalAnalysisWorker(use_aws=True)
    return _worker


def _parse_body(raw: str) -> dict:
    body = json.loads(raw)
    if isinstance(body.get("Message"), str):
        body = json.loads(body["Message"])
    return body


def handler(event, context):
    batch_failures = []
    worker = _get_worker()
    for record in event.get("Records", []):
        mid = record.get("messageId") or ""
        try:
            body = _parse_body(record["body"])
            job_id = body.get("job_id") or body.get("id")
            if not job_id:
                raise ValueError("SQS body missing job_id")
            sk = body.get("s3_key") or body.get("audio_s3_key")
            sk = str(sk).strip() if sk else None

            result = worker.process_job(str(job_id), s3_key=sk)
            if result.get("status") not in ("success", "skipped"):
                raise RuntimeError(result.get("error") or "process_job failed")
        except Exception:
            traceback.print_exc()
            batch_failures.append({"itemIdentifier": mid})
    return {"batchItemFailures": batch_failures}

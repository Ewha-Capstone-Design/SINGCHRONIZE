"""
보컬 분석 단계별 소요 시간 로그 (CloudWatch / 로컬 공통)

환경변수 VOCAL_ANALYSIS_TIMING_LOG=0 이면 비활성화 (기본: 켜짐).

로그 형식 예:
  [VOCAL_TIMING] job_id=... phase=s3_download event=START ts=2026-04-04T12:00:00.000Z
  [VOCAL_TIMING] job_id=... phase=s3_download event=END elapsed_ms=1234 ts=...

p50/p95: CloudWatch Logs Insights 등에서 phase·elapsed_ms 파싱.
"""
from __future__ import annotations

import contextvars
import os
import time
from datetime import datetime, timezone
from typing import Dict, Tuple

_starts: Dict[Tuple[str, str], float] = {}
_current_job_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "vocal_timing_job_id", default=""
)


def timing_enabled() -> bool:
    raw = (os.getenv("VOCAL_ANALYSIS_TIMING_LOG") or "1").strip().lower()
    return raw not in ("0", "false", "no", "off", "")


def timing_job_token(job_id: str):
    """process_job 등 상위에서 with timing_job_token(jid): ... 로 스코프 설정."""
    return _current_job_id.set(job_id or "")


def timing_job_reset(token) -> None:
    _current_job_id.reset(token)


def current_job_id() -> str:
    return (_current_job_id.get() or "").strip() or "-"


def log_phase(phase: str, event: str, *, job_id: str | None = None, note: str = "") -> None:
    if not timing_enabled():
        return
    jid = (job_id or current_job_id()).strip() or "-"
    ev = event.strip().upper()
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    key = (jid, phase)
    extra = f" {note}" if note else ""

    if ev == "START":
        _starts[key] = time.perf_counter()
        print(f"[VOCAL_TIMING] job_id={jid} phase={phase} event=START ts={now_iso}{extra}")
        return

    if ev == "END":
        t0 = _starts.pop(key, None)
        elapsed_ms = (
            int((time.perf_counter() - t0) * 1000) if t0 is not None else -1
        )
        print(
            f"[VOCAL_TIMING] job_id={jid} phase={phase} event=END "
            f"elapsed_ms={elapsed_ms} ts={now_iso}{extra}"
        )
        return

    print(f"[VOCAL_TIMING] job_id={jid} phase={phase} event={ev} ts={now_iso}{extra}")

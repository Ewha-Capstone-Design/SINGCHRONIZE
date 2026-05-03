"""ECS Fargate RunTask 호출 — Lambda 디스패처에서 공통 사용."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict

import boto3


def _utc_iso_ms() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def run_worker_task(
    *,
    task_definition: str,
    container_name: str,
    environment: Dict[str, str],
) -> str:
    """
    환경변수( Lambda 설정 ):
      ECS_CLUSTER, ECS_SUBNETS (쉼표 구분), ECS_SECURITY_GROUPS (쉼표 구분)
      ECS_ASSIGN_PUBLIC_IP — ENABLED | DISABLED (기본 ENABLED)
      ECS_PLATFORM_VERSION — 비우면 생략 (예: 1.4.0)
    """
    ecs = boto3.client("ecs")
    cluster = os.environ["ECS_CLUSTER"]
    subnets = [s.strip() for s in os.environ["ECS_SUBNETS"].split(",") if s.strip()]
    security_groups = [
        s.strip() for s in os.environ["ECS_SECURITY_GROUPS"].split(",") if s.strip()
    ]
    assign_public_ip = os.environ.get("ECS_ASSIGN_PUBLIC_IP", "ENABLED").upper()
    if assign_public_ip not in ("ENABLED", "DISABLED"):
        assign_public_ip = "ENABLED"

    env_pairs = [
        {"name": k, "value": str(v)}
        for k, v in environment.items()
        if v is not None and str(v) != ""
    ]

    kwargs: Dict = {
        "cluster": cluster,
        "taskDefinition": task_definition,
        "launchType": "FARGATE",
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "subnets": subnets,
                "securityGroups": security_groups,
                "assignPublicIp": assign_public_ip,
            }
        },
        "overrides": {
            "containerOverrides": [
                {
                    "name": container_name,
                    "environment": env_pairs,
                }
            ]
        },
    }
    platform_version = (os.environ.get("ECS_PLATFORM_VERSION") or "").strip()
    if platform_version:
        kwargs["platformVersion"] = platform_version

    resp = ecs.run_task(**kwargs)
    fails = resp.get("failures") or []
    if fails:
        raise RuntimeError(f"ECS RunTask failures: {fails}")
    tasks = resp.get("tasks") or []
    if not tasks:
        raise RuntimeError("ECS RunTask returned no tasks")
    task_arn = tasks[0]["taskArn"]
    job_id = (environment.get("JOB_ID") or environment.get("job_id") or "-").strip()
    print(
        f"[ECS_DISPATCH] event=RunTask_submitted ts={_utc_iso_ms()} cluster={cluster} "
        f"task_arn={task_arn} task_definition={task_definition} job_id={job_id}",
        flush=True,
    )
    return task_arn

#!/usr/bin/env bash
# ECS RunTask ZIP 디스패처는 폐지됨 — Lambda 컨테이너는 sqs_direct 사용.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${DIR}/dist"
mkdir -p "$OUT"
echo "OK: ECS 디스패처 ZIP 은 더 이상 생성하지 않습니다."
echo "    추천·보컬 Lambda: ${DIR}/../sqs_direct/deploy_lambda_containers.sh"
echo "    (참고) ecs_run_task.py 는 다른 용도로만 사용 시 레포에 유지."
exit 0

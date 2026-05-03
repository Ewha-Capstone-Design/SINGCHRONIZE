#!/bin/bash
# 보컬 분석 워커 이미지 — ECR 빌드·푸시 + ECS 태스크 정의 등록.
# ECS 서비스(SQS --queue 직접 소비)용. 스모크: DEPLOY_SMOKE_TEST_JOB_ID=<analysis_jobs.id> 시 RunTask 1회(JOB_ID 주입).
# 사용법: cd ai && ./deploy-vocal-analysis-worker.sh
# (선택) VOCAL_ANALYSIS_SQS_QUEUE_URL=https://sqs...  를 export 하면 태스크 정의 environment 에 주입됩니다.

set -e

AWS_REGION="${AWS_REGION:-ap-northeast-2}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"
ECR_REPOSITORY="vocal-analysis-worker"
ECS_CLUSTER="${ECS_CLUSTER:-singchronize-cluster}"
ECS_TASK_DEFINITION="vocal-analysis-worker"
TASK_DEF_FILE="ecs-task-definition.vocal_analysis_worker.json"
SUBNET_IDS="${SUBNET_IDS:-subnet-xxx,subnet-yyy}"
SECURITY_GROUP_ID="${SECURITY_GROUP_ID:-sg-xxx}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}보컬 분석 워커 ECS 배포${NC}"

if [ -z "$AWS_ACCOUNT_ID" ]; then
  AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || true)
  if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}AWS_ACCOUNT_ID를 설정하거나 AWS CLI 프로필을 구성하세요.${NC}"
    exit 1
  fi
fi
echo -e "${GREEN}계정: $AWS_ACCOUNT_ID${NC}"

echo -e "\n${YELLOW}[1] ECR 로그인${NC}"
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo -e "\n${YELLOW}[2] ECR 리포지토리 확인${NC}"
if ! aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" &>/dev/null; then
  aws ecr create-repository --repository-name "$ECR_REPOSITORY" --region "$AWS_REGION"
fi

echo -e "\n${YELLOW}[3] Docker 빌드 (ECAPA 프리패치에 네트워크 필요)${NC}"
docker build -f Dockerfile.vocal_analysis_worker -t "$ECR_REPOSITORY:latest" .

ECR_IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest"
docker tag "$ECR_REPOSITORY:latest" "$ECR_IMAGE_URI"

echo -e "\n${YELLOW}[4] ECR 푸시${NC}"
docker push "$ECR_IMAGE_URI"

echo -e "\n${YELLOW}[5] 태스크 정의 등록${NC}"
TMP_DEF="$(mktemp)"
sed "s|YOUR_ACCOUNT_ID|$AWS_ACCOUNT_ID|g" "$TASK_DEF_FILE" > "$TMP_DEF"
if [ -n "${VOCAL_ANALYSIS_SQS_QUEUE_URL:-}" ]; then
  TMP_JQ="$(mktemp)"
  if jq --arg url "$VOCAL_ANALYSIS_SQS_QUEUE_URL" \
    '.containerDefinitions[0].environment += [{"name":"VOCAL_ANALYSIS_SQS_QUEUE_URL","value":$url}] | .containerDefinitions[0].environment |= unique_by(.name)' \
    "$TMP_DEF" > "$TMP_JQ" 2>/dev/null; then
    mv "$TMP_JQ" "$TMP_DEF"
  else
    rm -f "$TMP_JQ"
    echo -e "${YELLOW}jq 없음 — VOCAL_ANALYSIS_SQS_QUEUE_URL 는 ECS 콘솔·태스크 정의에서 수동 설정하세요.${NC}"
  fi
fi
aws ecs register-task-definition --cli-input-json "file://$TMP_DEF" --region "$AWS_REGION"
rm -f "$TMP_DEF"

echo -e "\n${YELLOW}[6] Fargate 스모크 실행 (선택)${NC}"
if [ -z "${DEPLOY_SMOKE_TEST_JOB_ID:-}" ]; then
  echo -e "${YELLOW}건너뜀: DEPLOY_SMOKE_TEST_JOB_ID 가 비어 있음. 운영은 ECS 서비스(--queue) 또는 수동 RunTask.${NC}"
else
  # 서비스 기본 CMD는 --queue 이므로 스모크는 1건 처리 CMD로 덮어씀
  OVERRIDES="{\"containerOverrides\":[{\"name\":\"vocal-analysis-worker\",\"command\":[\"python\",\"vocal_analysis_worker.py\"],\"environment\":[{\"name\":\"JOB_ID\",\"value\":\"${DEPLOY_SMOKE_TEST_JOB_ID}\"}]}]}"
  TASK_ARN=$(aws ecs run-task \
    --cluster "$ECS_CLUSTER" \
    --task-definition "$ECS_TASK_DEFINITION" \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
    --overrides "$OVERRIDES" \
    --region "$AWS_REGION" \
    --query 'tasks[0].taskArn' \
    --output text)

  if [ "$TASK_ARN" != "None" ] && [ -n "$TASK_ARN" ]; then
    echo -e "${GREEN}Task ARN: $TASK_ARN${NC}"
    echo -e "\n${YELLOW}로그:${NC} aws logs tail /ecs/vocal-analysis-worker --follow --region $AWS_REGION"
  else
    echo -e "${RED}태스크 실행 실패${NC}"
    exit 1
  fi
fi

echo -e "\n${GREEN}완료${NC}"

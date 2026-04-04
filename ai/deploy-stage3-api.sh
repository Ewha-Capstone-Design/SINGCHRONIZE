#!/usr/bin/env bash
# stage3-api → ECR 푸시 + ECS Task Definition 등록
# ALB/서비스는 VPC·서브넷·보안그룹마다 달라 콘솔 또는 별도 CLI로 연결 (아래 DEPLOY_STAGE3.md 참고)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

AWS_REGION="${AWS_REGION:-ap-northeast-2}"
ECR_NAME="${ECR_NAME:-stage3-api}"
CLUSTER_NAME="${CLUSTER_NAME:-singchronize-cluster}"
TASK_DEF_FILE="${TASK_DEF_FILE:-ecs-task-definition.stage3_api.json}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text 2>/dev/null || true)}"
if [[ -z "$AWS_ACCOUNT_ID" || "$AWS_ACCOUNT_ID" == "None" ]]; then
  echo -e "${RED}AWS CLI 로그인 후 다시 실행하세요.${NC}"
  exit 1
fi

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_NAME}"

echo -e "${GREEN}Account ${AWS_ACCOUNT_ID} / Region ${AWS_REGION}${NC}"

echo -e "\n${YELLOW}[1/5] ECR 로그인${NC}"
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo -e "\n${YELLOW}[2/5] ECR 리포지토리 확인${NC}"
if ! aws ecr describe-repositories --repository-names "$ECR_NAME" --region "$AWS_REGION" &>/dev/null; then
  aws ecr create-repository --repository-name "$ECR_NAME" --region "$AWS_REGION"
  echo -e "${GREEN}리포지토리 생성: ${ECR_NAME}${NC}"
else
  echo -e "${GREEN}리포지토리 존재${NC}"
fi

echo -e "\n${YELLOW}[3/5] Docker 빌드 (linux/arm64 — Fargate ARM 태스크 정의와 일치)${NC}"
docker buildx version &>/dev/null || { echo -e "${RED}docker buildx 필요합니다.${NC}"; exit 1; }
docker buildx build --platform linux/arm64 \
  -f stage3-api/Dockerfile \
  -t "${ECR_NAME}:latest" \
  --load \
  stage3-api

echo -e "\n${YELLOW}[4/5] 태그 & 푸시${NC}"
docker tag "${ECR_NAME}:latest" "${ECR_URI}:latest"
docker push "${ECR_URI}:latest"
echo -e "${GREEN}푸시 완료: ${ECR_URI}:latest${NC}"

echo -e "\n${YELLOW}[5/5] Task Definition 등록${NC}"
TMP_DEF="$(mktemp)"
sed "s|YOUR_ACCOUNT_ID|${AWS_ACCOUNT_ID}|g" "$TASK_DEF_FILE" > "$TMP_DEF"
echo -e "${YELLOW}확인: ${TASK_DEF_FILE} 의 executionRoleArn, taskRoleArn, secrets valueFrom 이 실제 ARN 인지 검토하세요.${NC}"
aws ecs register-task-definition --cli-input-json "file://${TMP_DEF}" --region "$AWS_REGION"
rm -f "$TMP_DEF"
echo -e "${GREEN}등록 완료 (family: stage3-api)${NC}"

echo -e "\n${GREEN}다음 단계:${NC}"
echo "  1) CloudWatch 로그 그룹 없으면: aws logs create-log-group --log-group-name /ecs/stage3-api --region $AWS_REGION"
echo "  2) ALB + Target Group(IP, 포트 8000, 헬스 /health) 생성 — ai/DEPLOY_STAGE3.md"
echo "  3) ECS 서비스 생성: cluster=$CLUSTER_NAME, task=stage3-api, desired-count=1, 로드밸런서 연결"

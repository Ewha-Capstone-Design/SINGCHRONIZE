#!/bin/bash
# 추천 워커 이미지 — ECR 빌드/푸시 + ECS 태스크 정의 등록. SQS는 Lambda 디스패처가 소비 후 RunTask로 1건 실행.
# 스모크 테스트: DEPLOY_SMOKE_TEST_JOB_ID=<recommendation_logs.id> 가 있으면 RunTask 1회(환경변수 JOB_ID 주입).
# 사용법: cd ai && ./deploy-recommendation-worker.sh

set -e

AWS_REGION="${AWS_REGION:-ap-northeast-2}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"
ECR_REPOSITORY="recommendation-worker"
ECS_CLUSTER="${ECS_CLUSTER:-singchronize-cluster}"
ECS_TASK_DEFINITION="recommendation-worker"
TASK_DEF_FILE="ecs-task-definition.recommendation_worker.json"
SUBNET_IDS="${SUBNET_IDS:-subnet-0b15fa0e11dd0fb7d,subnet-0ab5015861b51eccd}"
SECURITY_GROUP_ID="${SECURITY_GROUP_ID:-sg-08d77fdd77ad00b56}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}추천 워커 ECS 배포${NC}"

if [ -z "$AWS_ACCOUNT_ID" ]; then
  AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || true)
  if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}AWS_ACCOUNT_ID를 설정하거나 AWS CLI 프로필을 구성하세요.${NC}"
    exit 1
  fi
fi
echo -e "${GREEN}계정: $AWS_ACCOUNT_ID${NC}"

echo -e "\n${YELLOW}[0] 필수 시크릿 확인${NC}"
for secret_name in \
  singchronize/mongo-uri \
  singchronize/mongo-db-name; do
  if ! aws secretsmanager describe-secret --secret-id "$secret_name" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo -e "${RED}필수 시크릿 없음: $secret_name${NC}"
    echo -e "${YELLOW}먼저 생성 후 다시 실행하세요.${NC}"
    exit 1
  fi
done
echo -e "${GREEN}필수 시크릿 확인 완료${NC}"

echo -e "\n${YELLOW}[1] CloudWatch 로그 그룹 확인${NC}"
if ! aws logs describe-log-groups --log-group-name-prefix "/ecs/recommendation-worker" --region "$AWS_REGION" --query "logGroups[?logGroupName=='/ecs/recommendation-worker'].logGroupName" --output text | grep -q "/ecs/recommendation-worker"; then
  aws logs create-log-group --log-group-name "/ecs/recommendation-worker" --region "$AWS_REGION" || true
fi

echo -e "\n${YELLOW}[2] ECR 로그인${NC}"
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo -e "\n${YELLOW}[3] ECR 리포지토리 확인${NC}"
if ! aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" &>/dev/null; then
  aws ecr create-repository --repository-name "$ECR_REPOSITORY" --region "$AWS_REGION"
fi

echo -e "\n${YELLOW}[4] Docker 빌드${NC}"
docker build -f Dockerfile.recommendation_worker -t "$ECR_REPOSITORY:latest" .

ECR_IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest"
docker tag "$ECR_REPOSITORY:latest" "$ECR_IMAGE_URI"

echo -e "\n${YELLOW}[5] ECR 푸시${NC}"
docker push "$ECR_IMAGE_URI"

echo -e "\n${YELLOW}[6] 태스크 정의 등록${NC}"
TMP_DEF="$(mktemp)"
sed "s|YOUR_ACCOUNT_ID|$AWS_ACCOUNT_ID|g" "$TASK_DEF_FILE" > "$TMP_DEF"
aws ecs register-task-definition --cli-input-json "file://$TMP_DEF" --region "$AWS_REGION" >/dev/null
rm -f "$TMP_DEF"

echo -e "\n${YELLOW}[7] Fargate 스모크 실행 (선택)${NC}"
if [ -z "${DEPLOY_SMOKE_TEST_JOB_ID:-}" ]; then
  echo -e "${YELLOW}건너뜀: DEPLOY_SMOKE_TEST_JOB_ID 가 비어 있음. 운영은 Lambda→RunTask.${NC}"
else
  OVERRIDES="{\"containerOverrides\":[{\"name\":\"recommendation-worker\",\"environment\":[{\"name\":\"JOB_ID\",\"value\":\"${DEPLOY_SMOKE_TEST_JOB_ID}\"}]}]}"
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
    echo -e "\n${YELLOW}로그:${NC} aws logs tail /ecs/recommendation-worker --follow --region $AWS_REGION"
  else
    echo -e "${RED}태스크 실행 실패${NC}"
    exit 1
  fi
fi

echo -e "\n${GREEN}추천 워커 배포 완료${NC}"

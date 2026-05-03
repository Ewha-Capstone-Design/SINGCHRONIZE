#!/bin/bash
# AWS ECS Fargate 배포 스크립트
# 사용법: ./deploy-to-aws.sh

set -e

# 설정 변수 (필요시 수정)
AWS_REGION="ap-northeast-2"
AWS_ACCOUNT_ID=""  # AWS 계정 ID 입력 필요
ECR_REPOSITORY="song-feature-worker"
ECS_CLUSTER="singchronize-cluster"
ECS_TASK_DEFINITION="song-feature-worker"
SUBNET_IDS="subnet-xxx,subnet-yyy"  # VPC 서브넷 ID (쉼표로 구분)
SECURITY_GROUP_ID="sg-xxx"  # 보안 그룹 ID

# 색상 출력
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 AWS ECS Fargate 배포 시작${NC}"

# 1. AWS 계정 ID 확인
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${YELLOW}⚠️  AWS_ACCOUNT_ID가 설정되지 않았습니다.${NC}"
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        echo -e "${RED}❌ AWS 계정 ID를 찾을 수 없습니다. AWS CLI가 설정되어 있는지 확인하세요.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ AWS 계정 ID: $AWS_ACCOUNT_ID${NC}"
fi

# 2. ECR 로그인
echo -e "\n${YELLOW}[Step 1] ECR 로그인...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
echo -e "${GREEN}✓ ECR 로그인 완료${NC}"

# 3. ECR 리포지토리 생성 (없는 경우)
echo -e "\n${YELLOW}[Step 2] ECR 리포지토리 확인/생성...${NC}"
if ! aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION &>/dev/null; then
    echo -e "${YELLOW}리포지토리가 없어서 생성합니다...${NC}"
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
    echo -e "${GREEN}✓ ECR 리포지토리 생성 완료${NC}"
else
    echo -e "${GREEN}✓ ECR 리포지토리 존재 확인${NC}"
fi

# 4. Docker 이미지 빌드
echo -e "\n${YELLOW}[Step 3] Docker 이미지 빌드...${NC}"
docker build -f Dockerfile.song_feature_worker -t $ECR_REPOSITORY:latest .
echo -e "${GREEN}✓ 이미지 빌드 완료${NC}"

# 5. 이미지 태깅
ECR_IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest"
echo -e "\n${YELLOW}[Step 4] 이미지 태깅...${NC}"
docker tag $ECR_REPOSITORY:latest $ECR_IMAGE_URI
echo -e "${GREEN}✓ 이미지 태깅 완료: $ECR_IMAGE_URI${NC}"

# 6. ECR에 이미지 푸시
echo -e "\n${YELLOW}[Step 5] ECR에 이미지 푸시...${NC}"
docker push $ECR_IMAGE_URI
echo -e "${GREEN}✓ 이미지 푸시 완료${NC}"

# 7. ECS Task Definition 업데이트
echo -e "\n${YELLOW}[Step 6] ECS Task Definition 업데이트...${NC}"
# 이미지 URI를 task definition에 반영
sed "s|YOUR_ACCOUNT_ID|$AWS_ACCOUNT_ID|g" ecs-task-definition.json > /tmp/task-def.json
sed -i.bak "s|YOUR_ACCOUNT_ID|$AWS_ACCOUNT_ID|g" /tmp/task-def.json 2>/dev/null || sed -i '' "s|YOUR_ACCOUNT_ID|$AWS_ACCOUNT_ID|g" /tmp/task-def.json

aws ecs register-task-definition --cli-input-json file:///tmp/task-def.json --region $AWS_REGION
echo -e "${GREEN}✓ Task Definition 등록 완료${NC}"

# 8. ECS Task 실행
echo -e "\n${YELLOW}[Step 7] ECS Task 실행...${NC}"
TASK_ARN=$(aws ecs run-task \
    --cluster $ECS_CLUSTER \
    --task-definition $ECS_TASK_DEFINITION \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
    --region $AWS_REGION \
    --query 'tasks[0].taskArn' \
    --output text)

if [ "$TASK_ARN" != "None" ] && [ -n "$TASK_ARN" ]; then
    echo -e "${GREEN}✓ Task 실행 완료${NC}"
    echo -e "${GREEN}Task ARN: $TASK_ARN${NC}"
    echo -e "\n${YELLOW}📊 로그 확인:${NC}"
    echo "aws logs tail /ecs/song-feature-worker --follow --region $AWS_REGION"
    echo -e "\n${YELLOW}📊 Task 상태 확인:${NC}"
    echo "aws ecs describe-tasks --cluster $ECS_CLUSTER --tasks $TASK_ARN --region $AWS_REGION"
else
    echo -e "${RED}❌ Task 실행 실패${NC}"
    exit 1
fi

echo -e "\n${GREEN}✅ 배포 완료!${NC}"






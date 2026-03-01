#!/bin/bash
# AWS 전체 설정 및 배포 자동화 스크립트
# AWS CLI 설치부터 배포까지 모든 것을 자동으로 처리

set -e

# 설정 변수
AWS_REGION="ap-northeast-2"
ECR_REPOSITORY="song-feature-worker"
ECS_CLUSTER="singchronize-cluster"
ECS_TASK_DEFINITION="song-feature-worker"

# 색상 출력
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AWS ECS Fargate 자동 설정 및 배포 스크립트          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"

# ============================================
# Step 1: AWS CLI 설치 확인 및 설치
# ============================================
echo -e "${YELLOW}[Step 1] AWS CLI 확인 및 설치...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${YELLOW}AWS CLI가 설치되어 있지 않습니다. 설치를 시작합니다...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            echo -e "${YELLOW}Homebrew를 사용하여 AWS CLI 설치...${NC}"
            brew install awscli
        else
            echo -e "${RED}❌ Homebrew가 설치되어 있지 않습니다.${NC}"
            echo -e "${YELLOW}다음 명령어로 Homebrew를 설치하거나, AWS CLI를 수동으로 설치하세요:${NC}"
            echo -e "${BLUE}/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ macOS가 아닌 시스템입니다. AWS CLI를 수동으로 설치하세요.${NC}"
        echo -e "${YELLOW}https://aws.amazon.com/cli/ 에서 설치 방법을 확인하세요.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ AWS CLI 설치 확인됨${NC}"
    aws --version
fi

# ============================================
# Step 2: AWS 자격 증명 확인
# ============================================
echo -e "\n${YELLOW}[Step 2] AWS 자격 증명 확인...${NC}"

if ! aws sts get-caller-identity &>/dev/null; then
    echo -e "${RED}❌ AWS 자격 증명이 설정되어 있지 않습니다.${NC}"
    echo -e "${YELLOW}AWS 자격 증명을 설정하세요:${NC}"
    echo -e "${BLUE}aws configure${NC}"
    echo -e "\n${YELLOW}또는 환경 변수로 설정:${NC}"
    echo -e "${BLUE}export AWS_ACCESS_KEY_ID=your-access-key${NC}"
    echo -e "${BLUE}export AWS_SECRET_ACCESS_KEY=your-secret-key${NC}"
    echo -e "${BLUE}export AWS_DEFAULT_REGION=ap-northeast-2${NC}"
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS 계정 ID: $AWS_ACCOUNT_ID${NC}"

# ============================================
# Step 3: .env 파일에서 환경 변수 읽기
# ============================================
echo -e "\n${YELLOW}[Step 3] 환경 변수 파일(.env) 확인...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env 파일이 없습니다.${NC}"
    exit 1
fi

# .env 파일에서 값 추출
SUPABASE_URL=$(grep "^SUPABASE_URL=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "")
SUPABASE_SERVICE_ROLE_KEY=$(grep "^SUPABASE_SERVICE_ROLE_KEY=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "")
AWS_ACCESS_KEY_ID_ENV=$(grep "^AWS_ACCESS_KEY_ID=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "")
AWS_SECRET_ACCESS_KEY_ENV=$(grep "^AWS_SECRET_ACCESS_KEY=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "")
S3_BUCKET_NAME=$(grep "^S3_BUCKET_NAME=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "")
DB_HOST=$(grep "^DB_HOST=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "")
DB_NAME=$(grep "^DB_NAME=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "")
DB_USER=$(grep "^DB_USER=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "")
DB_PASSWORD=$(grep "^DB_PASSWORD=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "")
DB_PORT=$(grep "^DB_PORT=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "5432")

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_ROLE_KEY" ] || [ -z "$S3_BUCKET_NAME" ]; then
    echo -e "${RED}❌ .env 파일에 필요한 환경 변수가 없습니다.${NC}"
    echo -e "${YELLOW}필수 변수: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, S3_BUCKET_NAME${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 환경 변수 로드 완료${NC}"

# ============================================
# Step 4: VPC 및 서브넷 자동 찾기
# ============================================
echo -e "\n${YELLOW}[Step 4] VPC 및 서브넷 찾기...${NC}"

# 기본 VPC 찾기
DEFAULT_VPC=$(aws ec2 describe-vpcs \
    --filters "Name=isDefault,Values=true" \
    --query 'Vpcs[0].VpcId' \
    --output text \
    --region $AWS_REGION 2>/dev/null || echo "")

if [ -z "$DEFAULT_VPC" ] || [ "$DEFAULT_VPC" == "None" ]; then
    # 기본 VPC가 없으면 첫 번째 VPC 사용
    DEFAULT_VPC=$(aws ec2 describe-vpcs \
        --query 'Vpcs[0].VpcId' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "")
fi

if [ -z "$DEFAULT_VPC" ] || [ "$DEFAULT_VPC" == "None" ]; then
    echo -e "${RED}❌ VPC를 찾을 수 없습니다. AWS 콘솔에서 VPC를 생성하세요.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ VPC 찾음: $DEFAULT_VPC${NC}"

# 서브넷 찾기 (퍼블릭 서브넷 우선)
SUBNETS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$DEFAULT_VPC" \
    --query 'Subnets[*].SubnetId' \
    --output text \
    --region $AWS_REGION 2>/dev/null || echo "")

if [ -z "$SUBNETS" ]; then
    echo -e "${RED}❌ 서브넷을 찾을 수 없습니다.${NC}"
    exit 1
fi

# 첫 2개 서브넷 사용 (없으면 1개만)
SUBNET_ARRAY=($SUBNETS)
if [ ${#SUBNET_ARRAY[@]} -ge 2 ]; then
    SUBNET_IDS="${SUBNET_ARRAY[0]},${SUBNET_ARRAY[1]}"
else
    SUBNET_IDS="${SUBNET_ARRAY[0]}"
fi

echo -e "${GREEN}✓ 서브넷 찾음: $SUBNET_IDS${NC}"

# 보안 그룹 찾기 또는 생성
SECURITY_GROUP=$(aws ec2 describe-security-groups \
    --filters "Name=vpc-id,Values=$DEFAULT_VPC" "Name=group-name,Values=ecs-singchronize-worker" \
    --query 'SecurityGroups[0].GroupId' \
    --output text \
    --region $AWS_REGION 2>/dev/null || echo "")

if [ -z "$SECURITY_GROUP" ] || [ "$SECURITY_GROUP" == "None" ]; then
    echo -e "${YELLOW}보안 그룹이 없어서 생성합니다...${NC}"
    SECURITY_GROUP=$(aws ec2 create-security-group \
        --group-name ecs-singchronize-worker \
        --description "Security group for ECS Fargate song feature worker" \
        --vpc-id $DEFAULT_VPC \
        --query 'GroupId' \
        --output text \
        --region $AWS_REGION)
    
    # 아웃바운드 규칙 추가 (모든 트래픽 허용)
    aws ec2 authorize-security-group-egress \
        --group-id $SECURITY_GROUP \
        --protocol -1 \
        --cidr 0.0.0.0/0 \
        --region $AWS_REGION &>/dev/null || true
    
    echo -e "${GREEN}✓ 보안 그룹 생성 완료: $SECURITY_GROUP${NC}"
else
    echo -e "${GREEN}✓ 보안 그룹 찾음: $SECURITY_GROUP${NC}"
fi

# ============================================
# Step 5: ECS 클러스터 생성
# ============================================
echo -e "\n${YELLOW}[Step 5] ECS 클러스터 확인/생성...${NC}"

if ! aws ecs describe-clusters --clusters $ECS_CLUSTER --region $AWS_REGION --query 'clusters[0].status' --output text 2>/dev/null | grep -q "ACTIVE"; then
    echo -e "${YELLOW}클러스터가 없어서 생성합니다...${NC}"
    aws ecs create-cluster --cluster-name $ECS_CLUSTER --region $AWS_REGION
    echo -e "${GREEN}✓ ECS 클러스터 생성 완료${NC}"
else
    echo -e "${GREEN}✓ ECS 클러스터 존재 확인${NC}"
fi

# ============================================
# Step 6: CloudWatch Logs 그룹 생성
# ============================================
echo -e "\n${YELLOW}[Step 6] CloudWatch Logs 그룹 확인/생성...${NC}"

LOG_GROUP="/ecs/song-feature-worker"
if ! aws logs describe-log-groups --log-group-name-prefix $LOG_GROUP --region $AWS_REGION --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "$LOG_GROUP"; then
    echo -e "${YELLOW}로그 그룹이 없어서 생성합니다...${NC}"
    aws logs create-log-group --log-group-name $LOG_GROUP --region $AWS_REGION
    echo -e "${GREEN}✓ CloudWatch Logs 그룹 생성 완료${NC}"
else
    echo -e "${GREEN}✓ CloudWatch Logs 그룹 존재 확인${NC}"
fi

# ============================================
# Step 7: Secrets Manager에 시크릿 저장
# ============================================
echo -e "\n${YELLOW}[Step 7] Secrets Manager에 시크릿 저장...${NC}"

create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if aws secretsmanager describe-secret --secret-id $secret_name --region $AWS_REGION &>/dev/null; then
        echo -e "${YELLOW}  $secret_name 업데이트 중...${NC}"
        aws secretsmanager update-secret \
            --secret-id $secret_name \
            --secret-string "$secret_value" \
            --region $AWS_REGION &>/dev/null
        echo -e "${GREEN}  ✓ $secret_name 업데이트 완료${NC}"
    else
        echo -e "${YELLOW}  $secret_name 생성 중...${NC}"
        aws secretsmanager create-secret \
            --name $secret_name \
            --secret-string "$secret_value" \
            --region $AWS_REGION &>/dev/null
        echo -e "${GREEN}  ✓ $secret_name 생성 완료${NC}"
    fi
}

create_or_update_secret "singchronize/supabase-url" "$SUPABASE_URL"
create_or_update_secret "singchronize/supabase-service-role-key" "$SUPABASE_SERVICE_ROLE_KEY"

if [ -n "$AWS_ACCESS_KEY_ID_ENV" ] && [ -n "$AWS_SECRET_ACCESS_KEY_ENV" ]; then
    create_or_update_secret "singchronize/aws-access-key-id" "$AWS_ACCESS_KEY_ID_ENV"
    create_or_update_secret "singchronize/aws-secret-access-key" "$AWS_SECRET_ACCESS_KEY_ENV"
fi

create_or_update_secret "singchronize/s3-bucket-name" "$S3_BUCKET_NAME"

# DB 연결 정보 저장
if [ -n "$DB_HOST" ] && [ -n "$DB_NAME" ] && [ -n "$DB_USER" ] && [ -n "$DB_PASSWORD" ]; then
    create_or_update_secret "singchronize/db-host" "$DB_HOST"
    create_or_update_secret "singchronize/db-name" "$DB_NAME"
    create_or_update_secret "singchronize/db-user" "$DB_USER"
    create_or_update_secret "singchronize/db-password" "$DB_PASSWORD"
    create_or_update_secret "singchronize/db-port" "$DB_PORT"
else
    echo -e "${YELLOW}⚠️  DB 연결 정보가 .env에 없습니다. (선택사항)${NC}"
fi

# ============================================
# Step 8: ECR 리포지토리 생성
# ============================================
echo -e "\n${YELLOW}[Step 8] ECR 리포지토리 확인/생성...${NC}"

if ! aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION &>/dev/null; then
    echo -e "${YELLOW}리포지토리가 없어서 생성합니다...${NC}"
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
    echo -e "${GREEN}✓ ECR 리포지토리 생성 완료${NC}"
else
    echo -e "${GREEN}✓ ECR 리포지토리 존재 확인${NC}"
fi

# ============================================
# Step 9: Docker 이미지 빌드 및 푸시
# ============================================
echo -e "\n${YELLOW}[Step 9] Docker 이미지 빌드 및 푸시...${NC}"

# ECR 로그인
echo -e "${YELLOW}ECR 로그인 중...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
echo -e "${GREEN}✓ ECR 로그인 완료${NC}"

# 이미지 빌드 (linux/amd64 플랫폼으로 빌드 - ECS Fargate 호환)
echo -e "${YELLOW}Docker 이미지 빌드 중 (linux/amd64 플랫폼)...${NC}"
docker build --platform linux/amd64 -f Dockerfile.song_feature_worker -t $ECR_REPOSITORY:latest .
echo -e "${GREEN}✓ 이미지 빌드 완료${NC}"

# 이미지 태깅
ECR_IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest"
echo -e "${YELLOW}이미지 태깅 중...${NC}"
docker tag $ECR_REPOSITORY:latest $ECR_IMAGE_URI
echo -e "${GREEN}✓ 이미지 태깅 완료${NC}"

# 이미지 푸시
echo -e "${YELLOW}ECR에 이미지 푸시 중... (시간이 걸릴 수 있습니다)${NC}"
docker push $ECR_IMAGE_URI
echo -e "${GREEN}✓ 이미지 푸시 완료${NC}"

# ============================================
# Step 10: ECS Task Definition 등록
# ============================================
echo -e "\n${YELLOW}[Step 10] ECS Task Definition 등록...${NC}"

# Task Definition JSON 생성
TASK_DEF_FILE="/tmp/task-def-$$.json"
cat > $TASK_DEF_FILE <<EOF
{
  "family": "$ECS_TASK_DEFINITION",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "4096",
  "memory": "8192",
  "executionRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "song-feature-worker",
      "image": "$ECR_IMAGE_URI",
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "$LOG_GROUP",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        {
          "name": "PYTHONUNBUFFERED",
          "value": "1"
        },
        {
          "name": "PYTHONPATH",
          "value": "/app/scripts"
        }
      ],
      "secrets": [
        {
          "name": "SUPABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:singchronize/supabase-url"
        },
        {
          "name": "SUPABASE_SERVICE_ROLE_KEY",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:singchronize/supabase-service-role-key"
        },
        {
          "name": "S3_BUCKET_NAME",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:singchronize/s3-bucket-name"
        },
        {
          "name": "DB_HOST",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:singchronize/db-host"
        },
        {
          "name": "DB_NAME",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:singchronize/db-name"
        },
        {
          "name": "DB_USER",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:singchronize/db-user"
        },
        {
          "name": "DB_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:singchronize/db-password"
        },
        {
          "name": "DB_PORT",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:singchronize/db-port"
        }
      ],
      "command": [
        "python",
        "song_feature_worker.py",
        "--mode",
        "s3",
        "--unprocessed",
        "--limit",
        "500",
        "--upload-features-s3"
      ]
    }
  ]
}
EOF

# AWS_ACCESS_KEY_ID와 AWS_SECRET_ACCESS_KEY가 있으면 추가
if [ -n "$AWS_ACCESS_KEY_ID_ENV" ] && [ -n "$AWS_SECRET_ACCESS_KEY_ENV" ]; then
    # jq가 있으면 사용, 없으면 sed로 처리
    if command -v jq &> /dev/null; then
        jq '.containerDefinitions[0].secrets += [
            {
                "name": "AWS_ACCESS_KEY_ID",
                "valueFrom": "arn:aws:secretsmanager:'$AWS_REGION':'$AWS_ACCOUNT_ID':secret:singchronize/aws-access-key-id"
            },
            {
                "name": "AWS_SECRET_ACCESS_KEY",
                "valueFrom": "arn:aws:secretsmanager:'$AWS_REGION':'$AWS_ACCOUNT_ID':secret:singchronize/aws-secret-access-key"
            }
        ]' $TASK_DEF_FILE > $TASK_DEF_FILE.tmp && mv $TASK_DEF_FILE.tmp $TASK_DEF_FILE
    fi
fi

# DB 정보가 없으면 Task Definition에서 제거 (Secrets Manager에 없으면 에러 발생)
if [ -z "$DB_HOST" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    echo -e "${YELLOW}⚠️  DB 정보가 없어서 Task Definition에서 DB secrets를 제거합니다.${NC}"
    if command -v jq &> /dev/null; then
        jq '.containerDefinitions[0].secrets = (.containerDefinitions[0].secrets | map(select(.name | test("^DB_") | not)))' $TASK_DEF_FILE > $TASK_DEF_FILE.tmp && mv $TASK_DEF_FILE.tmp $TASK_DEF_FILE
    fi
fi

# Task Definition 등록
aws ecs register-task-definition --cli-input-json file://$TASK_DEF_FILE --region $AWS_REGION
echo -e "${GREEN}✓ Task Definition 등록 완료${NC}"

# ============================================
# Step 11: IAM 역할 확인 및 생성
# ============================================
echo -e "\n${YELLOW}[Step 11] IAM 역할 확인...${NC}"

# ECS Task Execution Role 확인
EXECUTION_ROLE="ecsTaskExecutionRole"
if ! aws iam get-role --role-name $EXECUTION_ROLE &>/dev/null; then
    echo -e "${YELLOW}ECS Task Execution Role이 없습니다.${NC}"
    echo -e "${YELLOW}다음 명령어로 역할을 생성하세요:${NC}"
    echo -e "${BLUE}aws iam create-role --role-name $EXECUTION_ROLE --assume-role-policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"ecs-tasks.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}'${NC}"
    echo -e "${BLUE}aws iam attach-role-policy --role-name $EXECUTION_ROLE --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy${NC}"
    echo -e "${BLUE}aws iam attach-role-policy --role-name $EXECUTION_ROLE --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite${NC}"
fi

# ============================================
# Step 12: ECS Task 실행
# ============================================
echo -e "\n${YELLOW}[Step 12] ECS Task 실행...${NC}"

TASK_ARN=$(aws ecs run-task \
    --cluster $ECS_CLUSTER \
    --task-definition $ECS_TASK_DEFINITION \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP],assignPublicIp=ENABLED}" \
    --region $AWS_REGION \
    --query 'tasks[0].taskArn' \
    --output text 2>/dev/null || echo "")

if [ -z "$TASK_ARN" ] || [ "$TASK_ARN" == "None" ]; then
    echo -e "${RED}❌ Task 실행 실패${NC}"
    echo -e "${YELLOW}에러를 확인하세요:${NC}"
    aws ecs run-task \
        --cluster $ECS_CLUSTER \
        --task-definition $ECS_TASK_DEFINITION \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP],assignPublicIp=ENABLED}" \
        --region $AWS_REGION 2>&1 || true
    exit 1
fi

echo -e "${GREEN}✓ Task 실행 완료!${NC}"
echo -e "${GREEN}Task ARN: $TASK_ARN${NC}"

# ============================================
# 완료 메시지
# ============================================
echo -e "\n${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            ✅ 배포 완료!                                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}📊 모니터링 명령어:${NC}"
echo -e "${BLUE}# 실시간 로그 확인${NC}"
echo -e "aws logs tail $LOG_GROUP --follow --region $AWS_REGION\n"

echo -e "${BLUE}# Task 상태 확인${NC}"
echo -e "aws ecs describe-tasks --cluster $ECS_CLUSTER --tasks $TASK_ARN --region $AWS_REGION\n"

echo -e "${BLUE}# Task 목록 확인${NC}"
echo -e "aws ecs list-tasks --cluster $ECS_CLUSTER --region $AWS_REGION\n"

echo -e "${YELLOW}💰 예상 비용: 약 42시간 × \$0.045/시간 = 약 \$1.89 (약 2,500원)${NC}\n"


#!/bin/bash
# IAM 역할 생성 스크립트 (ECS Task 실행에 필요)

set -e

# 색상 출력
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# AWS CLI 확인
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI가 설치되어 있지 않습니다.${NC}"
    echo -e "${YELLOW}다음 명령어로 설치하세요:${NC}"
    echo -e "${BLUE}brew install awscli${NC}"
    echo -e "\n${YELLOW}또는 공식 설치 방법:${NC}"
    echo -e "${BLUE}curl \"https://awscli.amazonaws.com/AWSCLIV2.pkg\" -o \"AWSCLIV2.pkg\"${NC}"
    echo -e "${BLUE}sudo installer -pkg AWSCLIV2.pkg -target /${NC}"
    exit 1
fi

AWS_REGION="ap-northeast-2"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}❌ AWS 자격 증명이 설정되어 있지 않습니다.${NC}"
    echo -e "${YELLOW}다음 명령어로 설정하세요:${NC}"
    echo -e "${BLUE}aws configure${NC}"
    exit 1
fi

echo -e "${BLUE}IAM 역할 생성 중...${NC}\n"

# ECS Task Execution Role 생성
EXECUTION_ROLE="ecsTaskExecutionRole"
echo -e "${YELLOW}[1] ECS Task Execution Role 생성...${NC}"

if aws iam get-role --role-name $EXECUTION_ROLE &>/dev/null; then
    echo -e "${GREEN}✓ $EXECUTION_ROLE 이미 존재합니다${NC}"
else
    # 역할 생성
    aws iam create-role \
        --role-name $EXECUTION_ROLE \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Service": "ecs-tasks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }]
        }'
    echo -e "${GREEN}✓ $EXECUTION_ROLE 생성 완료${NC}"
fi

# 정책 연결
echo -e "${YELLOW}[2] 정책 연결...${NC}"

# ECS Task Execution Role Policy
aws iam attach-role-policy \
    --role-name $EXECUTION_ROLE \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy 2>/dev/null || echo "  (이미 연결됨)"

# Secrets Manager 읽기 권한
aws iam attach-role-policy \
    --role-name $EXECUTION_ROLE \
    --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite 2>/dev/null || echo "  (이미 연결됨)"

echo -e "${GREEN}✓ 정책 연결 완료${NC}"

# ECS Task Role 생성 (S3, Supabase 접근용)
TASK_ROLE="ecsTaskRole"
echo -e "\n${YELLOW}[3] ECS Task Role 생성...${NC}"

if aws iam get-role --role-name $TASK_ROLE &>/dev/null; then
    echo -e "${GREEN}✓ $TASK_ROLE 이미 존재합니다${NC}"
else
    # 역할 생성
    aws iam create-role \
        --role-name $TASK_ROLE \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Service": "ecs-tasks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }]
        }'
    echo -e "${GREEN}✓ $TASK_ROLE 생성 완료${NC}"
fi

# S3 전체 접근 정책 (필요시 더 제한적으로 변경 가능)
echo -e "${YELLOW}[4] S3 접근 정책 생성...${NC}"

S3_POLICY_NAME="ecsTaskS3Access"
S3_POLICY_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:policy/$S3_POLICY_NAME"

if ! aws iam get-policy --policy-arn $S3_POLICY_ARN &>/dev/null; then
    aws iam create-policy \
        --policy-name $S3_POLICY_NAME \
        --policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::singchronize-bucket/*",
                    "arn:aws:s3:::singchronize-bucket"
                ]
            }]
        }'
    echo -e "${GREEN}✓ S3 정책 생성 완료${NC}"
else
    echo -e "${GREEN}✓ S3 정책 이미 존재합니다${NC}"
fi

# 정책 연결
aws iam attach-role-policy \
    --role-name $TASK_ROLE \
    --policy-arn $S3_POLICY_ARN 2>/dev/null || echo "  (이미 연결됨)"

echo -e "\n${GREEN}✅ IAM 역할 생성 완료!${NC}\n"


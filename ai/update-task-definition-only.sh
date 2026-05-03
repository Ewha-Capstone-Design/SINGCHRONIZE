#!/bin/bash
# Task Definition만 업데이트 (이미지 빌드/푸시 없이)

set -e

AWS_REGION="ap-northeast-2"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECS_CLUSTER="singchronize-cluster"
ECS_TASK_DEFINITION="song-feature-worker"
LOG_GROUP="/ecs/song-feature-worker"
ECR_REPOSITORY="song-feature-worker"

# 색상 출력
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Task Definition 업데이트 (DB secrets 포함)${NC}\n"

# 현재 이미지 URI 가져오기
ECR_IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest"

# .env에서 DB 정보 읽기
if [ -f ".env" ]; then
    DB_HOST=$(grep "^DB_HOST=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "")
    DB_NAME=$(grep "^DB_NAME=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "")
    DB_USER=$(grep "^DB_USER=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "")
    DB_PASSWORD=$(grep "^DB_PASSWORD=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "")
    DB_PORT=$(grep "^DB_PORT=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "5432")
fi

# Task Definition JSON 생성
TASK_DEF_FILE="/tmp/task-def-update-$$.json"
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

# Task Definition 등록
echo -e "${YELLOW}Task Definition 등록 중...${NC}"
aws ecs register-task-definition --cli-input-json file://$TASK_DEF_FILE --region $AWS_REGION
echo -e "${GREEN}✓ Task Definition 등록 완료${NC}"

echo -e "\n${GREEN}✅ 완료! 이제 새 Task를 실행하세요:${NC}"
echo -e "${BLUE}aws ecs run-task --cluster $ECS_CLUSTER --task-definition $ECS_TASK_DEFINITION:2 --launch-type FARGATE --network-configuration \"awsvpcConfiguration={subnets=[subnet-0b15fa0e11dd0fb7d,subnet-0ab5015861b51eccd],securityGroups=[sg-0af8c00b9e9c78b7c],assignPublicIp=ENABLED}\" --region $AWS_REGION${NC}"






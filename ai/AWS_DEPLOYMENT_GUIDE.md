# AWS ECS Fargate 배포 가이드

이 가이드는 `song-feature-worker`를 AWS ECS Fargate에서 실행하는 방법을 설명합니다.

## 사전 준비

### 1. AWS CLI 설정
```bash
# AWS CLI 설치 확인
aws --version

# AWS 자격 증명 설정
aws configure
```

### 2. 필요한 AWS 리소스

#### ECR 리포지토리
- 자동 생성됨 (스크립트에서 처리)

#### ECS 클러스터
```bash
# 클러스터 생성
aws ecs create-cluster --cluster-name singchronize-cluster --region ap-northeast-2
```

#### VPC 및 네트워크
- **서브넷 ID**: Fargate Task가 실행될 서브넷 (최소 2개 권장)
- **보안 그룹 ID**: 
  - 아웃바운드: 인터넷 접근 (HTTPS, S3, Supabase)
  - 인바운드: 필요 없음 (워커는 외부에서 접근 불필요)

#### Secrets Manager (환경 변수 저장)
```bash
# Supabase URL
aws secretsmanager create-secret \
  --name singchronize/supabase-url \
  --secret-string "https://your-project.supabase.co" \
  --region ap-northeast-2

# Supabase Service Role Key
aws secretsmanager create-secret \
  --name singchronize/supabase-service-role-key \
  --secret-string "your-service-role-key" \
  --region ap-northeast-2

# AWS Access Key ID
aws secretsmanager create-secret \
  --name singchronize/aws-access-key-id \
  --secret-string "your-access-key-id" \
  --region ap-northeast-2

# AWS Secret Access Key
aws secretsmanager create-secret \
  --name singchronize/aws-secret-access-key \
  --secret-string "your-secret-access-key" \
  --region ap-northeast-2

# S3 Bucket Name
aws secretsmanager create-secret \
  --name singchronize/s3-bucket-name \
  --secret-string "singchronize-bucket" \
  --region ap-northeast-2
```

#### CloudWatch Logs
```bash
# 로그 그룹 생성
aws logs create-log-group \
  --log-group-name /ecs/song-feature-worker \
  --region ap-northeast-2
```

## 배포 방법

### 방법 1: 자동 배포 스크립트 (권장)

1. **스크립트 수정**
   ```bash
   # deploy-to-aws.sh 파일 열기
   # 다음 변수들을 수정:
   # - AWS_REGION: 리전 (기본값: ap-northeast-2)
   # - SUBNET_IDS: 서브넷 ID (쉼표로 구분)
   # - SECURITY_GROUP_ID: 보안 그룹 ID
   ```

2. **스크립트 실행**
   ```bash
   chmod +x deploy-to-aws.sh
   ./deploy-to-aws.sh
   ```

### 방법 2: 수동 배포

#### Step 1: ECR에 이미지 푸시
```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin \
  YOUR_ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 빌드
docker build -f Dockerfile.song_feature_worker -t song-feature-worker:latest .

# 이미지 태깅
docker tag song-feature-worker:latest \
  YOUR_ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com/song-feature-worker:latest

# 이미지 푸시
docker push \
  YOUR_ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com/song-feature-worker:latest
```

#### Step 2: Task Definition 등록
```bash
# ecs-task-definition.json 파일 수정:
# - YOUR_ACCOUNT_ID를 실제 계정 ID로 변경
# - Secrets Manager ARN을 실제 ARN으로 변경

# Task Definition 등록
aws ecs register-task-definition \
  --cli-input-json file://ecs-task-definition.json \
  --region ap-northeast-2
```

#### Step 3: Task 실행
```bash
aws ecs run-task \
  --cluster singchronize-cluster \
  --task-definition song-feature-worker \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --region ap-northeast-2
```

## 모니터링

### CloudWatch Logs 확인
```bash
# 실시간 로그 스트리밍
aws logs tail /ecs/song-feature-worker --follow --region ap-northeast-2

# 최근 로그 확인
aws logs tail /ecs/song-feature-worker --since 1h --region ap-northeast-2
```

### Task 상태 확인
```bash
# Task 목록 조회
aws ecs list-tasks --cluster singchronize-cluster --region ap-northeast-2

# Task 상세 정보
aws ecs describe-tasks \
  --cluster singchronize-cluster \
  --tasks TASK_ARN \
  --region ap-northeast-2
```

### Task 중지
```bash
aws ecs stop-task \
  --cluster singchronize-cluster \
  --task TASK_ARN \
  --region ap-northeast-2
```

## 비용 예상

### ECS Fargate 비용 (ap-northeast-2 기준)
- **CPU**: 4 vCPU = $0.04048/시간
- **Memory**: 8 GB = $0.004445/시간
- **총합**: 약 **$0.044925/시간** (약 55원/시간)

### 500곡 처리 예상 비용
- **예상 시간**: 약 42시간 (한 곡당 5분)
- **총 비용**: 약 **$1.89** (약 2,500원)

### 추가 비용
- **ECR**: 이미지 저장 (GB당 $0.10/월, 무시 가능)
- **CloudWatch Logs**: 로그 저장 (GB당 $0.50)
- **Data Transfer**: S3 다운로드/업로드 (GB당 $0.09)

## 병렬 처리 (성능 향상)

여러 Task를 동시에 실행하여 처리 시간을 단축할 수 있습니다:

```bash
# 5개 Task 동시 실행 (각각 100곡씩 처리)
for i in {1..5}; do
  aws ecs run-task \
    --cluster singchronize-cluster \
    --task-definition song-feature-worker \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
    --overrides "{\"containerOverrides\":[{\"name\":\"song-feature-worker\",\"command\":[\"python\",\"song_feature_worker.py\",\"--mode\",\"s3\",\"--unprocessed\",\"--limit\",\"100\",\"--offset\",\"$((($i-1)*100))\",\"--upload-features-s3\"]}]}" \
    --region ap-northeast-2 &
done
```

**주의**: `--offset` 옵션이 `song_feature_worker.py`에 구현되어 있어야 합니다.

## 트러블슈팅

### Task가 시작되지 않음
- VPC 서브넷이 인터넷 접근 가능한지 확인
- 보안 그룹에서 아웃바운드 규칙 확인
- Secrets Manager에 시크릿이 올바르게 저장되어 있는지 확인

### Task가 즉시 종료됨
- CloudWatch Logs에서 에러 메시지 확인
- 환경 변수가 올바르게 설정되었는지 확인

### 이미지 pull 실패
- ECR 리포지토리 권한 확인
- Task Execution Role에 ECR 권한이 있는지 확인

## 다음 단계

1. **ECS Service로 전환**: Task를 Service로 전환하여 자동 재시작 및 스케일링
2. **SQS 연동**: 큐 기반 작업 분배
3. **EventBridge 스케줄링**: 주기적 배치 작업 실행
4. **Auto Scaling**: 작업량에 따른 자동 스케일링






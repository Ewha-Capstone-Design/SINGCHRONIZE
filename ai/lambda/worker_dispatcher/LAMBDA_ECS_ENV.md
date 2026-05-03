# Lambda — SQS 직접 처리 (컨테이너 이미지)

ECS `RunTask` 디스패처(ZIP)는 **폐지**되었습니다. 추천·보컬 모두 **SQS → Lambda(컨테이너)** 로 동일 메시지 계약을 처리합니다.

## 배포

```bash
cd ai
./lambda/sqs_direct/deploy_lambda_containers.sh          # 추천 + 보컬 ECR 푸시
./lambda/sqs_direct/deploy_lambda_containers.sh recommendation
./lambda/sqs_direct/deploy_lambda_containers.sh vocal
```

- **Dockerfile**: `lambda/sqs_direct/Dockerfile.recommendation`, `Dockerfile.vocal`
- **핸들러**: `recommendation.handler`, `vocal.handler` (이미지 안에서 각각 `recommendation.py`, `vocal.py` 로 복사됨)
- **ECR 리포지토리**(스크립트 기본): `singchronize-recommendation-lambda`, `singchronize-vocal-lambda`

## Lambda 콘솔에서 설정

| 항목 | 추천 | 보컬 |
|------|------|------|
| 패키지 유형 | 컨테이너 이미지 | 컨테이너 이미지 |
| 타임아웃 | 5~15분(부하에 맞게) | 3~15분 |
| 메모리 | 1024~3008MB | 3008~10240MB |
| Ephemeral storage | 512MB 기본 | **10240MB 권장**(대용량 JSON·임시 파일) |
| 트리거 | 기존 추천 SQS 큐 | 기존 보컬 SQS 큐 |

환경 변수·시크릿은 **기존 ECS 태스크와 동일**하게 맞추면 됩니다 (`SUPABASE_*`, `S3_BUCKET_NAME`, `MONGO_*` 등).  
보컬은 Lambda에서 `/var/task` 가 읽기 전용이므로, 중간 산출물은 **`/tmp/vocal_worker_output`** 을 씁니다(`AWS_LAMBDA_FUNCTION_NAME` 설정 시 자동). 필요 시 `VOCAL_ANALYSIS_OUTPUT_ROOT` 로 덮어쓸 수 있습니다.

## 레거시 ECS

태스크 정의·클러스터는 롤백용으로 남겨둘 수 있으나, 운영 트래픽은 위 Lambda 로만내면 **SQS 트리거·Lambda·ECS RunTask 가 중복되지 않도록** 기존 디스패처 Lambda 는 비활성화하세요.

## 참고 파일

- `lambda/sqs_direct/recommendation_handler.py` — 추천 처리
- `lambda/sqs_direct/vocal_handler.py` — 보컬 처리
- `lambda/worker_dispatcher/ecs_run_task.py` — 다른 용도로만 참고 (디스패처 ZIP 은 `build.sh` 가 더 이상 생성하지 않음)

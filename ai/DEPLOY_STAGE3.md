# stage3-api ECS + ALB 배포

Fargate(ARM64)에서 FastAPI(포트 **8000**)를 띄우고, **ALB**로 HTTP(S) 노출하는 절차입니다. 리전 예시는 `ap-northeast-2` 입니다.

## `deploy-stage3-api.sh` 끝난 뒤 할 일 (순서대로)

1. **CloudWatch 로그 그룹** (없을 때만)

   ```bash
   aws logs create-log-group --log-group-name /ecs/stage3-api --region ap-northeast-2
   ```

2. **보안 그룹 2개**  
   - `sg-alb`: 인바운드 80·443, 아웃바운드 → 태스크 SG의 8000  
   - `sg-task`: 인바운드 8000 **출처 = sg-alb**, 아웃바운드 HTTPS(443)

3. **Target Group** (EC2 콘솔)  
   - 타입: **IP addresses**  
   - 포트 **8000**, VPC는 ECS 태스크와 동일  
   - Health check: **HTTP** `/health`, 포트 **8000**

4. **ALB**  
   - Listener 80 또는 443 → 위 Target Group으로 forward  
   - ALB에 **sg-alb** 연결

5. **ECS → 클러스터 → Create Service**  
   - Task: `stage3-api` 최신 revision  
   - 네트워크: 서브넷 2개 + **sg-task**  
   - Load balancer: 위 TG, 컨테이너 **stage3-api:8000**  
   - 프라이빗 서브넷이면 NAT 또는 퍼블릭 IP 정책에 맞게 `assignPublicIp` 설정

6. **백엔드 `.env`** 에 `STAGE3_API_BASE_URL` 설정 (아래 §6)

## 흐름

```text
인터넷/백엔드 → ALB:443(또는 80) → Target Group → 태스크 IP:8000 → uvicorn
```

## 사전 준비

1. **ECS 클러스터** (예: `singchronize-cluster`)
2. **VPC** + 퍼블릭 또는 프라이빗 서브넷 2개 이상(서비스용)
3. **Secrets Manager**에 `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` 저장  
   - `ecs-task-definition.stage3_api.json`의 `valueFrom`은 **전체 ARN**(끝에 `-xxxxx` 접미사 포함)으로 맞춰야 합니다.
4. **IAM**
   - `ecsTaskExecutionRole`: ECR pull, CloudWatch Logs, Secrets Manager 읽기
   - `ecsTaskRole`: stage3-api는 DB가 외부(Supabase)라 보통 비어 있어도 됨(팀 정책에 맞게)
5. **CloudWatch Logs**

```bash
aws logs create-log-group --log-group-name /ecs/stage3-api --region ap-northeast-2
```

## 1) 이미지 빌드 · ECR · 태스크 정의

저장소에서:

```bash
cd ai
chmod +x deploy-stage3-api.sh
# 필요 시: export AWS_REGION=ap-northeast-2
./deploy-stage3-api.sh
```

- `ecs-task-definition.stage3_api.json` 안의 `YOUR_ACCOUNT_ID`는 스크립트가 치환합니다.
- **역할 ARN·시크릿 ARN**은 콘솔 값과 일치하는지 수동 확인하세요.

인텔 맥 등에서 ARM 빌드가 실패하면 Docker Desktop의 buildx/에뮬레이션을 켜거나, 태스크 정의의 `cpuArchitecture`를 `X86_64`로 바꾼 뒌 `linux/amd64`로 빌드하세요.

## 2) 보안 그룹

| 리소스 | 인바운드 | 아웃바운드 |
|--------|----------|------------|
| **ALB** | 80, 443 (고정 IP/VPC/전체 — 정책에 맞게) | 태스크 SG의 **8000** |
| **태스크** | ALB SG에서 온 **8000**만 | 443 (Supabase 등 HTTPS) |

## 3) Target Group (ALB용)

콘솔: **EC2 → Target Groups → Create**

- **Target type**: IP addresses (Fargate `awsvpc` 필수)
- **Protocol / Port**: HTTP, **8000**
- **VPC**: 태스크와 동일
- **Health checks**: HTTP, 경로 **`/health`**, 포트 **8000** (또는 “Traffic port” 사용)
- Healthy threshold / interval은 기본값으로 시작 후 조정

## 4) Application Load Balancer

콘솔: **EC2 → Load Balancers → Create ALB**

- Scheme: internet-facing(공개) 또는 internal(백엔드만)
- **Listener**: 443(ACM 인증서) 또는 80
- **Default action**: 위에서 만든 Target Group으로 forward

(HTTPS를 쓰면 ACM에서 도메인 인증서를 같은 리전에 발급합니다.)

## 5) ECS Service 생성

콘솔: **ECS → Clusters → 서비스 Create**

- Launch type: **Fargate**
- Task definition: `stage3-api` (최신 리비전)
- Desired tasks: **1** 이상
- **Subnets / Security groups**: 태스크용 SG(위 표)
- 퍼블릭 서브넷 + NAT 없으면 **Assign public IP** 필요 여부를 네트워크 설계에 맞게 선택
- **Load balancing**: Application Load Balancer, Target Group 선택, **container name** `stage3-api`, **port** `8000`

CLI 예시(값은 본인 환경으로 교체):

```bash
aws ecs create-service \
  --cluster singchronize-cluster \
  --service-name stage3-api \
  --task-definition stage3-api \
  --desired-count 1 \
  --launch-type FARGATE \
  --platform-version LATEST \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-aaa,subnet-bbb],securityGroups=[sg-task],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:ap-northeast-2:ACCOUNT:targetgroup/stage3-api-tg/xxx,containerName=stage3-api,containerPort=8000" \
  --region ap-northeast-2
```

## 6) 백엔드 연동 (이 레포)

배포 후 ALB 주소(또는 내부 DNS)를 백엔드 `.env`에 넣습니다.

```env
# 예: https://stage3-xxxxx.ap-northeast-2.elb.amazonaws.com  (끝에 슬래시 없이)
STAGE3_API_BASE_URL=https://your-alb-dns-name.ap-northeast-2.elb.amazonaws.com
STAGE3_API_TIMEOUT_SECONDS=2
```

앱 API (로그인 필요):

- `POST /api/v1/recommendations/stage3/similar-voice-picks`
- Body: `{ "period": "week", "limit": 10 }` (선택: `interaction_since`, `interaction_until`)
- 응답: `source` 가 `stage3` / `fallback_stage2` / `unconfigured`, `results`: `[{ "song_id", "score" }]`

stage3 ECS가 죽었거나 타임아웃이면 **최근 DONE** 추천 job의 `recommended_songs`에서 곡을 풀어 폴백합니다.

직접 ECS만 때릴 때는:

- URL: `https://your-alb-dns/.../stage3/similar-voice-picks` (POST, JSON에 `user_id` 포함)

## 7) 확인

```bash
curl -sS "https://<ALB_DNS>/health"
curl -sS "https://<ALB_DNS>/stage3/similar-voice-picks" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"<uuid>","period":"week","limit":5}'
```

로그:

```bash
aws logs tail /ecs/stage3-api --follow --region ap-northeast-2
```

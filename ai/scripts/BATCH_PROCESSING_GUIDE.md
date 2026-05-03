# 500곡 배치 처리 가이드

## 개요

`song_feature_worker.py`를 사용하여 DB에 있는 모든 곡을 자동으로 처리하는 방법입니다.

## 기능

1. **처리되지 않은 곡 자동 감지**: `song_features` 테이블에 없는 곡만 처리
2. **배치 처리**: 여러 곡을 순차적으로 처리
3. **도커 지원**: 로컬 환경 없이 도커로 실행 가능

## 사용 방법

### 방법 1: 로컬에서 직접 실행

#### 모든 처리되지 않은 곡 처리
```bash
cd ai/scripts
python song_feature_worker.py --mode s3 --unprocessed
```

#### 최대 500곡만 처리
```bash
python song_feature_worker.py --mode s3 --unprocessed --limit 500
```

#### 특정 곡 ID 리스트 처리
```bash
python song_feature_worker.py --mode s3 --song-ids <id1> <id2> <id3>
```

### 방법 2: 도커로 실행 (권장)

#### 1. 도커 이미지 빌드
```bash
cd ai
docker build -f Dockerfile.song_feature_worker -t song-feature-worker .
```

#### 2. 도커로 실행 (모든 처리되지 않은 곡)
```bash
docker run --rm \
  --env-file .env \
  -v $(pwd)/artifacts:/app/scripts/artifacts \
  song-feature-worker \
  python song_feature_worker.py --unprocessed
```

#### 3. 최대 500곡만 처리
```bash
docker run --rm \
  --env-file .env \
  -v $(pwd)/artifacts:/app/scripts/artifacts \
  song-feature-worker \
  python song_feature_worker.py --unprocessed --limit 500
```

#### 4. Docker Compose 사용 (더 간단)
```bash
cd ai
docker-compose -f docker-compose.song_feature_worker.yml up
```

Docker Compose에서 명령어를 변경하려면 `docker-compose.song_feature_worker.yml` 파일의 `command` 주석을 해제하고 수정하세요.

## 환경 변수 설정

`.env` 파일에 다음 변수들이 설정되어 있어야 합니다:

```bash
# S3 설정
S3_BUCKET_NAME=your-bucket-name

# Supabase 설정
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# PostgreSQL 직접 연결 (song_features 테이블 저장용)
DB_HOST=your-db-host
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password
```

## 처리 시간 예상

- **1곡당 약 2-5분** (보컬 분리 + 특징 추출)
- **500곡**: 약 **17-42시간** (순차 처리 기준)
- 실제 시간은 곡 길이, 서버 성능에 따라 다름

## 모니터링

처리 중인 곡의 진행 상황은 콘솔에 출력됩니다:
```
[1/500] song_id=xxx-xxx-xxx
[2/500] song_id=yyy-yyy-yyy
...
```

처리 완료 후 요약이 출력됩니다:
```
✅ 성공: 495/500
❌ 실패: 5/500
```

## 주의사항

1. **인터넷 연결**: S3에서 곡을 다운로드하므로 안정적인 인터넷 연결 필요
2. **디스크 공간**: 임시 파일이 생성되므로 충분한 디스크 공간 필요 (곡당 약 100-500MB)
3. **메모리**: 보컬 분리와 특징 추출에 메모리가 많이 필요 (최소 4GB 권장)
4. **중단 시**: Ctrl+C로 중단 가능하지만, 이미 처리 중인 곡은 완료될 때까지 기다려야 함

## 재시작

처리 중 중단된 경우, 다시 `--unprocessed` 옵션으로 실행하면 이미 처리된 곡은 자동으로 스킵됩니다.

## 문제 해결

### "처리할 곡이 없습니다" 메시지
- 모든 곡이 이미 처리되었거나
- `songs` 테이블에 `raw_s3_key`가 없는 곡만 있는 경우

### 메모리 부족 에러
- 도커의 메모리 제한을 늘리거나 (`docker-compose.yml`에서 `memory` 조정)
- 한 번에 처리하는 곡 수를 줄이기 (`--limit` 옵션 사용)

### S3 다운로드 실패
- `.env`의 `S3_BUCKET_NAME` 확인
- AWS 자격 증명 확인 (환경 변수 또는 IAM 역할)






# 🚀 프로덕션 배포 가이드

## 📋 목차
1. [현재 상태 (테스트 단계)](#현재-상태-테스트-단계)
2. [프로덕션 아키텍처](#프로덕션-아키텍처)
3. [마이그레이션 체크리스트](#마이그레이션-체크리스트)
4. [AWS 연동 구현](#aws-연동-구현)
5. [DB 스키마 설계](#db-스키마-설계)

---

## 현재 상태 (테스트 단계)

### 🎯 목적
**보컬 분석 파이프라인의 성능 검증 및 최적화**

### 📁 현재 구조

```
로컬 파일 시스템
  ↓
test_single_file.py (테스트 스크립트)
  ↓
user_vocal_pipeline.py (핵심 분석 로직)
  ├─ audio_preprocessing.py
  ├─ feature_extraction.py
  └─ report_generator_v2.py
  ↓
로컬 JSON 파일 (test_output/)
```

### 🧪 테스트 방법

#### 1. 단일 파일 테스트
```bash
python test_single_file.py
```

#### 2. 워커 테스트 (프로덕션 시뮬레이션)
```bash
python test_worker.py
```

#### 3. CLI 테스트
```bash
python scripts/vocal_analysis_worker.py test_job_001 -a test_data/test2.m4a
```

### ✅ 현재 완료된 것
- [x] 아카펠라 전용 분석 파이프라인
- [x] 레이더 차트 5축 (V2)
- [x] 음역대, 음색 분석
- [x] 장르별 적합도 계산
- [x] ECAPA 임베딩 추출
- [x] 로컬 파일 기반 테스트
- [x] 워커 스켈레톤 코드

### ⏳ 아직 구현 안 된 것
- [ ] S3 연동
- [ ] DB 연동
- [ ] 에러 핸들링 (재시도 로직)
- [ ] 모니터링 및 로깅
- [ ] 성능 최적화 (배치 처리)

---

## 프로덕션 아키텍처

### 🏗️ 전체 흐름

```
[Frontend/Backend]
      ↓
   (1) 작업 생성
      ↓
   [Database]
   - job_id 생성
   - status: 'pending'
   - s3_audio_key 저장
      ↓
   (2) 워커 실행
      ↓
[Vocal Analysis Worker]
      ↓
   (3) S3에서 오디오 다운로드
      ↓
   (4) 보컬 분석 실행
   user_vocal_pipeline.py
      ↓
   (5) 결과를 DB에 저장
   - status: 'completed'
   - radar_chart 점수 (5축)
   - vocal_range
   - timbre_profile
   - genre_fitness
   - embedding
      ↓
[Frontend/Backend]
   (6) 결과 조회 및 표시
```

### 🔄 상세 워크플로우

#### Step 1: 작업 생성 (Backend)
```python
# Backend API
@app.post("/api/vocal-analysis/create")
def create_analysis_job(user_id: str, audio_file: UploadFile):
    # 1. S3에 오디오 업로드
    s3_key = f"users/{user_id}/audio_{timestamp}.m4a"
    s3.upload_fileobj(audio_file.file, BUCKET_NAME, s3_key)
    
    # 2. DB에 작업 생성
    job_id = str(uuid.uuid4())
    db.execute("""
        INSERT INTO vocal_analysis_jobs 
        (job_id, user_id, s3_audio_key, status, created_at)
        VALUES (%s, %s, %s, 'pending', NOW())
    """, (job_id, user_id, s3_key))
    
    # 3. 워커 트리거 (SQS, Lambda, ECS 등)
    trigger_worker(job_id)
    
    return {"job_id": job_id, "status": "pending"}
```

#### Step 2: 워커 실행
```python
# vocal_analysis_worker.py
worker = VocalAnalysisWorker(
    use_aws=True,
    s3_bucket="singchronize-audio",
    db_config={...}
)

result = worker.process_job(job_id)
```

#### Step 3: S3에서 다운로드
```python
def _download_from_s3(self, job_id: str) -> str:
    # DB에서 S3 키 조회
    s3_key = db.query("SELECT s3_audio_key FROM jobs WHERE job_id = %s", job_id)
    
    # S3에서 다운로드
    local_path = f"/tmp/{job_id}_audio.m4a"
    s3.download_file(BUCKET_NAME, s3_key, local_path)
    
    return local_path
```

#### Step 4: 보컬 분석 (기존 로직 그대로)
```python
# 이 부분은 이미 완성됨!
result = self.pipeline.process(audio_file, output_dir)
```

#### Step 5: DB에 저장
```python
def _save_to_db(self, job_id: str, result: Dict):
    radar = result['report']['radar_chart']
    vocal_range = result['report']['vocal_range']
    embedding = result['embedding']['representative_embedding']
    
    db.execute("""
        UPDATE vocal_analysis_jobs
        SET 
            status = 'completed',
            pitch_stability = %s,
            rhythm_stability = %s,
            dynamic_control = %s,
            vocal_clarity = %s,
            high_note_stability = %s,
            average_score = %s,
            lowest_note = %s,
            highest_note = %s,
            embedding = %s,
            result_json = %s,
            completed_at = NOW()
        WHERE job_id = %s
    """, (
        radar['pitch_stability'],
        radar['rhythm_stability'],
        radar['dynamic_control'],
        radar['vocal_clarity'],
        radar['high_note_stability'],
        radar['average'],
        vocal_range['lowest_note'],
        vocal_range['highest_note'],
        json.dumps(embedding),
        json.dumps(result),
        job_id
    ))
```

#### Step 6: 결과 조회 (Backend)
```python
@app.get("/api/vocal-analysis/{job_id}")
def get_analysis_result(job_id: str):
    result = db.query("""
        SELECT * FROM vocal_analysis_jobs WHERE job_id = %s
    """, job_id)
    
    if result['status'] == 'completed':
        return {
            "status": "completed",
            "radar_chart": {
                "pitch_stability": result['pitch_stability'],
                "rhythm_stability": result['rhythm_stability'],
                "dynamic_control": result['dynamic_control'],
                "vocal_clarity": result['vocal_clarity'],
                "high_note_stability": result['high_note_stability'],
                "average": result['average_score']
            },
            "vocal_range": {
                "lowest_note": result['lowest_note'],
                "highest_note": result['highest_note'],
                "range_semitones": result['range_semitones']
            },
            "timbre_summary": result['timbre_summary'],
            "genre_fitness": json.loads(result['genre_fitness_top3']),
            "full_result": json.loads(result['result_json'])
        }
    else:
        return {"status": result['status']}
```

---

## 마이그레이션 체크리스트

### Phase 1: 로컬 테스트 (현재) ✅
- [x] 분석 파이프라인 완성
- [x] 레이더 차트 검증
- [x] 성능 테스트
- [x] 워커 스켈레톤 코드

### Phase 2: AWS 연동 준비
- [ ] AWS 계정 및 권한 설정
- [ ] S3 버킷 생성
- [ ] RDS (PostgreSQL) 설정
- [ ] IAM 역할 및 정책

### Phase 3: 코드 수정
- [ ] `vocal_analysis_worker.py`에 S3 다운로드 구현
- [ ] `vocal_analysis_worker.py`에 DB 저장 구현
- [ ] 환경 변수 설정 (`.env`)
- [ ] 에러 핸들링 추가

### Phase 4: 인프라 구축
- [ ] EC2 또는 ECS 설정 (워커 실행 환경)
- [ ] SQS 또는 Lambda 트리거 설정
- [ ] CloudWatch 로깅 설정
- [ ] 모니터링 대시보드

### Phase 5: 통합 테스트
- [ ] End-to-End 테스트
- [ ] 부하 테스트
- [ ] 에러 시나리오 테스트

### Phase 6: 배포
- [ ] 스테이징 환경 배포
- [ ] 프로덕션 배포
- [ ] 모니터링 및 알림 설정

---

## AWS 연동 구현

### 1. S3 다운로드 구현

```python
# vocal_analysis_worker.py에 추가

import boto3
from botocore.exceptions import ClientError

def _download_from_s3(self, job_id: str) -> str:
    """S3에서 오디오 파일 다운로드"""
    try:
        # DB에서 S3 키 조회
        import psycopg2
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s3_audio_key FROM vocal_analysis_jobs 
            WHERE job_id = %s
        """, (job_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise ValueError(f"Job not found: {job_id}")
        
        s3_key = result[0]
        
        # S3에서 다운로드
        s3 = boto3.client('s3')
        local_path = f"/tmp/{job_id}_audio.m4a"
        
        print(f"  - S3 Bucket: {self.s3_bucket}")
        print(f"  - S3 Key: {s3_key}")
        print(f"  - Local Path: {local_path}")
        
        s3.download_file(
            Bucket=self.s3_bucket,
            Key=s3_key,
            Filename=local_path
        )
        
        print(f"✓ S3 다운로드 완료")
        return local_path
        
    except ClientError as e:
        print(f"❌ S3 다운로드 실패: {e}")
        raise
```

### 2. DB 저장 구현

```python
# vocal_analysis_worker.py에 추가

import psycopg2
import psycopg2.extras

def _save_to_db(self, job_id: str, result: Dict):
    """분석 결과를 DB에 저장"""
    try:
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # 레이더 차트
        radar = result['report']['radar_chart']
        
        # 음역대
        vocal_range = result['report']['vocal_range']
        
        # 음색 프로파일 (요약만 저장)
        timbre_profile = result['report']['timbre_profile']
        
        # 장르별 적합도 (TOP 3만 저장)
        genre_fitness = result['report']['genre_fitness']
        
        # 임베딩
        embedding = result['embedding']['representative_embedding']
        
        # 전체 결과 JSON
        result_json = json.dumps(result)
        
        # DB 업데이트
        cursor.execute("""
            UPDATE vocal_analysis_jobs
            SET 
                status = 'completed',
                pitch_stability = %s,
                rhythm_stability = %s,
                dynamic_control = %s,
                vocal_clarity = %s,
                high_note_stability = %s,
                average_score = %s,
                lowest_note = %s,
                lowest_hz = %s,
                highest_note = %s,
                highest_hz = %s,
                range_semitones = %s,
                timbre_summary = %s,
                genre_fitness_top3 = %s,
                embedding = %s,
                result_json = %s,
                completed_at = NOW(),
                updated_at = NOW()
            WHERE job_id = %s
        """, (
            radar['pitch_stability'],
            radar['rhythm_stability'],
            radar['dynamic_control'],
            radar['vocal_clarity'],
            radar['high_note_stability'],
            radar['average'],
            vocal_range['lowest_note'],
            vocal_range['lowest_hz'],
            vocal_range['highest_note'],
            vocal_range['highest_hz'],
            vocal_range['range_semitones'],
            timbre_profile.get('summary', ''),
            json.dumps(genre_fitness['top_genres']),
            json.dumps(embedding),
            result_json,
            job_id
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✓ DB 저장 완료")
        
    except Exception as e:
        print(f"❌ DB 저장 실패: {e}")
        raise
```

### 3. 환경 변수 설정

```bash
# .env 파일
AWS_REGION=ap-northeast-2
S3_BUCKET=singchronize-audio

DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=5432
DB_NAME=singchronize
DB_USER=admin
DB_PASSWORD=your-password

# 워커 설정
WORKER_CONCURRENCY=4
WORKER_TIMEOUT=300
```

```python
# vocal_analysis_worker.py에 추가

import os
from dotenv import load_dotenv

load_dotenv()

# 환경 변수에서 설정 로드
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

worker = VocalAnalysisWorker(
    use_aws=True,
    s3_bucket=os.getenv('S3_BUCKET'),
    db_config=db_config
)
```

---

## DB 스키마 설계

### 테이블: `vocal_analysis_jobs`

```sql
CREATE TABLE vocal_analysis_jobs (
    -- 기본 정보
    job_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    
    -- S3 정보
    s3_audio_key VARCHAR(255) NOT NULL,
    
    -- 상태
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- 'pending', 'processing', 'completed', 'failed'
    
    -- 레이더 차트 (5축)
    pitch_stability DECIMAL(5,2),
    rhythm_stability DECIMAL(5,2),
    dynamic_control DECIMAL(5,2),
    vocal_clarity DECIMAL(5,2),
    high_note_stability DECIMAL(5,2),
    average_score DECIMAL(5,2),
    
    -- 음역대
    lowest_note VARCHAR(10),
    lowest_hz DECIMAL(10,2),
    highest_note VARCHAR(10),
    highest_hz DECIMAL(10,2),
    range_semitones DECIMAL(5,2),
    
    -- 음색 프로파일 (요약)
    timbre_summary TEXT,
    
    -- 장르별 적합도 (TOP 3)
    genre_fitness_top3 TEXT,  -- JSON array
    
    -- 임베딩 (JSON 또는 별도 테이블)
    embedding TEXT,  -- JSON array
    
    -- 전체 결과 (JSON)
    result_json TEXT,
    
    -- 에러 정보
    error_message TEXT,
    
    -- 타임스탬프
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- 인덱스
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

### 테이블: `vocal_embeddings` (선택적)

임베딩을 별도 테이블로 관리하는 경우:

```sql
CREATE TABLE vocal_embeddings (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL REFERENCES vocal_analysis_jobs(job_id),
    embedding_vector FLOAT8[192],  -- PostgreSQL array
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    INDEX idx_job_id (job_id)
);

-- 벡터 유사도 검색을 위한 확장 (선택적)
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE vocal_embeddings 
ADD COLUMN embedding_pgvector vector(192);
```

---

## 배포 옵션

### 옵션 1: EC2 + Cron/Systemd
```bash
# EC2에 워커 배포
# crontab으로 주기적 실행
*/5 * * * * python /app/vocal_analysis_worker.py
```

**장점:**
- 간단한 구조
- 비용 저렴

**단점:**
- 수동 스케일링
- 장애 복구 어려움

---

### 옵션 2: ECS Fargate + SQS
```yaml
# ECS Task Definition
{
  "family": "vocal-analysis-worker",
  "containerDefinitions": [{
    "name": "worker",
    "image": "your-ecr/vocal-analysis:latest",
    "memory": 4096,
    "cpu": 2048,
    "environment": [
      {"name": "AWS_REGION", "value": "ap-northeast-2"},
      {"name": "S3_BUCKET", "value": "singchronize-audio"}
    ]
  }]
}
```

**장점:**
- 자동 스케일링
- 관리 용이
- 장애 복구 자동

**단점:**
- 비용 높음
- 설정 복잡

---

### 옵션 3: Lambda (권장하지 않음)
Lambda는 15분 제한이 있어 긴 오디오 처리에 부적합

---

## 모니터링 및 로깅

### CloudWatch 로깅
```python
import logging
import watchtower

# CloudWatch 핸들러 추가
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler(
    log_group='/aws/vocal-analysis-worker',
    stream_name='worker-{}'.format(os.getenv('HOSTNAME'))
))

# 로깅
logger.info(f"Job started: {job_id}")
logger.error(f"Job failed: {job_id}, error: {error}")
```

### 메트릭 수집
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# 성공/실패 카운트
cloudwatch.put_metric_data(
    Namespace='VocalAnalysis',
    MetricData=[
        {
            'MetricName': 'JobsCompleted',
            'Value': 1,
            'Unit': 'Count'
        }
    ]
)

# 처리 시간
cloudwatch.put_metric_data(
    Namespace='VocalAnalysis',
    MetricData=[
        {
            'MetricName': 'ProcessingTime',
            'Value': duration_seconds,
            'Unit': 'Seconds'
        }
    ]
)
```

---

## 성능 최적화

### 1. 배치 처리
```python
# 여러 작업을 한 번에 처리
worker.process_batch_jobs([
    {'job_id': 'job1', ...},
    {'job_id': 'job2', ...},
    {'job_id': 'job3', ...}
])
```

### 2. 캐싱 및 모델 재사용
```python
# ECAPA 모델은 이미 클래스 변수로 구현됨
# FeatureExtractor 클래스에서 자동으로 공유됨
# 첫 번째 인스턴스 생성 시 로드, 이후 모든 인스턴스가 재사용

# 구현 상태:
# - feature_extraction.py의 FeatureExtractor 클래스
# - _ecapa_classifier를 클래스 변수로 저장
# - 프로덕션 환경에서도 동일하게 작동
# - 메모리 효율성 및 속도 최적화 완료 ✅
```

### 3. 병렬 처리
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(worker.process_job, job['job_id'])
        for job in jobs
    ]
```

---

## 다음 단계

### 즉시 (현재 테스트 단계)
1. ✅ 로컬 파일로 성능 테스트
2. ✅ 레이더 차트 점수 검증
3. ✅ 워커 스켈레톤 코드 작성

### 단기 (AWS 연동 전)
1. 다양한 오디오 파일로 테스트
2. 엣지 케이스 처리 (짧은 오디오, 노이즈 등)
3. 에러 핸들링 강화

### 중기 (AWS 연동)
1. S3 다운로드 구현
2. DB 저장 구현
3. 통합 테스트

### 장기 (프로덕션 배포)
1. 인프라 구축 (ECS, SQS 등)
2. 모니터링 설정
3. 프로덕션 배포

---

## 참고 자료

- [AWS SDK for Python (Boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [PostgreSQL Python 드라이버 (psycopg2)](https://www.psycopg.org/docs/)
- [ECS Task Definition](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html)
- [CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html)


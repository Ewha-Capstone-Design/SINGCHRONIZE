# 📊 현재 상태 요약

## 🎯 프로젝트 목표

**보컬 분석 시스템의 성능 검증 및 최적화**

사용자가 아카펠라로 녹음한 음성을 분석하여:
- 레이더 차트 5축 점수 제공
- 음역대, 음색, 발성 기술 분석
- 추천 시스템용 임베딩 생성

---

## ✅ 완료된 것

### 1. 핵심 분석 파이프라인 ⭐
- [x] **아카펠라 전용 시스템** - MR 제거 불필요
- [x] **레이더 차트 V2** - 5축 (음정/리듬 안정도, 강약 조절, 발성 선명도, 고음 유지력)
- [x] **음역대 분석** - 최저음, 최고음, 테시투라
- [x] **음색 프로파일** - 7가지 음색 특성
- [x] **발성 기술 평가** - 레지스터, 기술, 공명
- [x] **비브라토 분석** - Rate, Extent, Regularity
- [x] **ECAPA 임베딩** - 192차원 음색 임베딩

### 2. 모듈 구조 ⭐
```
user_vocal_pipeline.py (메인)
  ├─ audio_preprocessing.py (전처리)
  ├─ feature_extraction.py (특징 추출)
  │   └─ advanced_vocal_analysis.py (고급 분석)
  └─ report_generator_v2.py (리포트 생성)
      └─ radar_chart_descriptions.py (설명)
```

### 3. 테스트 환경 ⭐
- [x] **test_single_file.py** - 단일 파일 테스트
- [x] **test_worker.py** - 워커 테스트 (프로덕션 시뮬레이션)
- [x] **vocal_analysis_worker.py** - 프로덕션용 워커 스켈레톤

### 4. 문서화 ⭐
- [x] **ACAPELLA_ONLY_GUIDE.md** - 아카펠라 가이드
- [x] **SYSTEM_SUMMARY.md** - 시스템 요약
- [x] **PRODUCTION_DEPLOYMENT_GUIDE.md** - 프로덕션 배포 가이드
- [x] **CURRENT_STATUS.md** - 현재 상태 (이 문서)

---

## 🎯 현재 단계: 성능 테스트 및 검증

### 테스트 방법

#### 1. 단일 파일 테스트
```bash
python test_single_file.py
```

**출력:**
- 레이더 차트 점수 (5축)
- 음역대 분석
- 음색 프로파일
- JSON 파일 (`test_output/test2_result.json`)

#### 2. 워커 테스트
```bash
python test_worker.py
```

**선택 옵션:**
1. 단일 작업 테스트
2. 배치 작업 테스트
3. 둘 다 실행

#### 3. CLI 테스트
```bash
python scripts/vocal_analysis_worker.py my_job_001 -a test_data/test2.m4a
```

---

## 📁 파일 구조

### 핵심 실행 파일
```
ai/
├── test_single_file.py          ⭐ 단일 파일 테스트
├── test_worker.py                ⭐ 워커 테스트
└── scripts/
    ├── user_vocal_pipeline.py    ⭐⭐⭐ 메인 파이프라인
    ├── vocal_analysis_worker.py  ⭐⭐ 프로덕션 워커
    ├── audio_preprocessing.py    전처리
    ├── feature_extraction.py     특징 추출
    ├── report_generator_v2.py    리포트 생성
    └── ...
```

### 문서
```
ai/
├── ACAPELLA_ONLY_GUIDE.md           아카펠라 가이드
├── SYSTEM_SUMMARY.md                시스템 요약
├── PRODUCTION_DEPLOYMENT_GUIDE.md   프로덕션 배포 가이드
├── CURRENT_STATUS.md                현재 상태 (이 문서)
└── docs/
    ├── SEGMENT_NORMALIZATION.md
    ├── RADAR_CHART_EVOLUTION.md
    └── ...
```

### 테스트 데이터
```
ai/
├── test_data/
│   ├── test1.m4a
│   └── test2.m4a
└── test_output/
    ├── test2_result.json         분석 결과
    └── test2_preprocessed.wav    전처리된 오디오
```

---

## 🚀 프로덕션 아키텍처 (미래)

### 현재 (테스트)
```
로컬 파일
  ↓
test_single_file.py
  ↓
user_vocal_pipeline.py
  ↓
로컬 JSON
```

### 미래 (프로덕션)
```
DB (job_id 조회)
  ↓
S3 (오디오 다운로드)
  ↓
vocal_analysis_worker.py
  ├─ user_vocal_pipeline.py (동일한 분석 로직!)
  └─ ...
  ↓
DB (결과 저장)
```

### 핵심 포인트
**`user_vocal_pipeline.py`의 분석 로직은 그대로 사용!**
- 현재 테스트로 성능 검증
- 나중에 워커에서 동일한 로직 호출
- 입력/출력 방식만 변경 (파일 → S3/DB)

---

## 📊 분석 결과 구조

### JSON 출력
```json
{
  "report": {
    "radar_chart": {
      "pitch_stability": 85.3,      // 음정 안정도
      "rhythm_stability": 78.9,     // 리듬 안정도
      "dynamic_control": 72.1,      // 강약 조절
      "vocal_clarity": 81.5,        // 발성 선명도
      "high_note_stability": 68.2,  // 고음 유지력
      "average": 77.2               // 평균
    },
    "vocal_range": {
      "lowest_note": "E3",
      "highest_note": "C5",
      "range_semitones": 20.0
    },
    "timbre_profile": {...},
    "vocal_technique": {...},
    "vibrato_analysis": {...}
  },
  "embedding": {
    "representative_embedding": [...],  // 192차원
    "embedding_dim": 192,
    "pitch_profile": {...},
    "timbre_vector": {...}
  },
  "metadata": {
    "duration": 45.2,
    "num_segments": 9,
    "sample_rate": 16000
  }
}
```

### DB 저장 (미래)
```sql
-- vocal_analysis_jobs 테이블
job_id                  VARCHAR(36)
user_id                 VARCHAR(36)
status                  VARCHAR(20)  -- 'completed'
pitch_stability         DECIMAL(5,2) -- 85.3
rhythm_stability        DECIMAL(5,2) -- 78.9
dynamic_control         DECIMAL(5,2) -- 72.1
vocal_clarity           DECIMAL(5,2) -- 81.5
high_note_stability     DECIMAL(5,2) -- 68.2
average_score           DECIMAL(5,2) -- 77.2
lowest_note             VARCHAR(10)  -- 'E3'
highest_note            VARCHAR(10)  -- 'C5'
embedding               TEXT         -- JSON array
result_json             TEXT         -- 전체 결과
```

---

## 🎯 레이더 차트 5축 상세

### 1. 음정 안정도 (Pitch Stability)
- **측정**: F0 변동 + 급변 구간 비율
- **기준**: F0 std < 20 cents = 90점 이상
- **의미**: 한 음을 얼마나 안정적으로 유지하는가

### 2. 리듬 안정도 (Rhythm Stability)
- **측정**: IOI 변동 + Tempo drift
- **기준**: IOI CV < 0.6 = 100점
- **의미**: 자기 템포를 얼마나 일정하게 유지하는가

### 3. 강약 조절 (Dynamic Control)
- **측정**: 다이나믹 범위 + RMS 부드러움
- **기준**: Dynamic range > 15dB = 100점
- **의미**: 소리 크기를 얼마나 자연스럽게 조절하는가

### 4. 발성 선명도 (Vocal Clarity)
- **측정**: HNR + Spectral Flatness + 에너지 안정성
- **기준**: HNR > 10dB = 80점 이상
- **의미**: 소리가 얼마나 또렷하고 깨끗한가

### 5. 고음 유지력 (High Note Stability)
- **측정**: 고음 구간 Pitch + HNR + 에너지
- **기준**: 고음 F0 변화율 < 2% = 80점 이상
- **의미**: 고음을 얼마나 안정적으로 유지하는가

---

## 🔧 성능 향상 장치

### 1. 세그먼트 기반 분석
- 20초 세그먼트, 5초 overlap
- 긴 오디오도 안정적 처리

### 2. Voiced 구간 필터링
- 무음/무성음 제거
- 실제 발성 구간만 분석

### 3. 이상치 제거
- 1st/99th percentile 사용
- 극단값 영향 최소화

### 4. 다중 지표 조합
- 각 축마다 2~3개 하위 지표
- 가중 평균으로 신뢰도 향상

### 5. 연속형 점수
- Binary 대신 연속형
- 미세한 차이도 반영

### 6. ECAPA 모델 재사용 (클래스 변수 공유)
- ECAPA-TDNN 모델을 클래스 변수로 저장
- 모든 FeatureExtractor 인스턴스가 동일한 모델 공유
- 첫 로드 후 재사용으로 메모리 효율성 및 속도 향상
- 프로덕션 환경에서도 동일하게 적용

---

## ⏳ 다음 단계

### Phase 1: 현재 (테스트 단계) ✅
```
목표: 분석 파이프라인 성능 검증

완료:
✅ 아카펠라 전용 시스템
✅ 레이더 차트 V2
✅ 로컬 파일 테스트
✅ 워커 스켈레톤

진행 중:
🔄 다양한 오디오로 테스트
🔄 엣지 케이스 검증
🔄 점수 신뢰도 확인
```

### Phase 2: AWS 연동 준비
```
목표: 프로덕션 환경 준비

TODO:
⏳ AWS 계정 및 권한 설정
⏳ S3 버킷 생성
⏳ RDS (PostgreSQL) 설정
⏳ IAM 역할 및 정책
```

### Phase 3: 코드 수정
```
목표: 워커에 AWS 연동 구현

TODO:
⏳ S3 다운로드 구현
⏳ DB 저장 구현
⏳ 환경 변수 설정
⏳ 에러 핸들링 추가
```

### Phase 4: 인프라 구축
```
목표: 워커 실행 환경 구축

TODO:
⏳ EC2 또는 ECS 설정
⏳ SQS 또는 Lambda 트리거
⏳ CloudWatch 로깅
⏳ 모니터링 대시보드
```

### Phase 5: 통합 테스트
```
목표: End-to-End 테스트

TODO:
⏳ 전체 흐름 테스트
⏳ 부하 테스트
⏳ 에러 시나리오 테스트
```

### Phase 6: 배포
```
목표: 프로덕션 배포

TODO:
⏳ 스테이징 환경 배포
⏳ 프로덕션 배포
⏳ 모니터링 및 알림
```

---

## 📝 사용 방법 (현재)

### 1. 환경 설정
```bash
# 가상환경 활성화
source venv/bin/activate

# 패키지 설치 (이미 완료)
pip install -r requirements.txt
```

### 2. 단일 파일 테스트
```bash
# 기본 테스트
python test_single_file.py

# 결과 확인
cat test_output/test2_result.json | jq '.report.radar_chart'
```

### 3. 워커 테스트
```bash
# 대화형 테스트
python test_worker.py

# CLI 테스트
python scripts/vocal_analysis_worker.py test_job_001 -a test_data/test2.m4a
```

### 4. Python 코드에서 사용
```python
import sys
sys.path.insert(0, 'scripts')

from user_vocal_pipeline import UserVocalPipeline

# 파이프라인 초기화
pipeline = UserVocalPipeline()

# 분석 실행
result = pipeline.process("my_acapella.wav")

# 결과 확인
print(result['report']['radar_chart'])
```

---

## 🎓 핵심 개념

### 안정도 vs 정확도

**안정도 (Stability)** ← 현재 측정 가능
- 자기 자신과의 비교
- "얼마나 일관되게 유지하는가?"
- 아카펠라에서 측정 가능

**정확도 (Accuracy)** ← 측정 불가능
- 정답과의 비교
- "정답과 얼마나 가까운가?"
- MR 필요 (아카펠라에서 불가능)

### 예시

**음정**
- 안정도: 한 음 내에서 F0 흔들림 정도
- 정확도: 정답 음과의 거리 (MR 필요)

**리듬**
- 안정도: 자기 템포를 얼마나 일정하게 유지하는가
- 정확도: 정답 박자와의 거리 (MR 필요)

---

## 📚 참고 문서

### 필수 문서 ⭐⭐⭐
1. **ACAPELLA_ONLY_GUIDE.md** - 아카펠라 가이드
2. **SYSTEM_SUMMARY.md** - 시스템 요약
3. **PRODUCTION_DEPLOYMENT_GUIDE.md** - 프로덕션 배포 가이드

### 상세 문서 ⭐⭐
4. **VOCAL_ANALYSIS_SYSTEM_DOCUMENTATION.md** - 전체 시스템 문서
5. **docs/SEGMENT_NORMALIZATION.md** - 세그먼트 정규화
6. **docs/RADAR_CHART_EVOLUTION.md** - 레이더 차트 진화

### 참고 문서 ⭐
7. **docs/STABILITY_VS_ACCURACY.md** - 안정도 vs 정확도
8. **docs/HYBRID_ANALYSIS_GUIDE.md** - 하이브리드 분석 (구버전)

---

## 🎯 요약

### 현재 상태
✅ **분석 파이프라인 완성** - 성능 테스트 중

### 핵심 파일
- `user_vocal_pipeline.py` - 메인 분석 로직 (완성!)
- `vocal_analysis_worker.py` - 프로덕션 워커 (스켈레톤)

### 테스트 방법
```bash
python test_single_file.py  # 단일 파일
python test_worker.py       # 워커 시뮬레이션
```

### 다음 단계
1. 🔄 다양한 오디오로 성능 테스트
2. ⏳ AWS 연동 준비
3. ⏳ 프로덕션 배포

### 핵심 포인트
**현재 테스트로 분석 로직 검증 → 나중에 워커에서 동일한 로직 사용!**

---

**마지막 업데이트:** 2024년 (아카펠라 전용 시스템 완성)


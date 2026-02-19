# 🎤 보컬 분석 시스템 (Vocal Analysis)

## 📋 개요

사용자 아카펠라 녹음을 분석하여 보컬 품질 리포트를 생성하는 시스템입니다.

---

## 📁 파일 구조

```
vocal_analysis/
├── __init__.py                      # Python 패키지
│
├── user_vocal_pipeline.py           ⭐⭐⭐ 메인 파이프라인
├── vocal_analysis_worker.py         ⭐⭐ 프로덕션 워커
│
├── audio_preprocessing.py           전처리 모듈
├── feature_extraction.py            특징 추출 모듈
├── advanced_vocal_analysis.py       고급 분석 모듈
├── report_generator_v2.py           리포트 생성 모듈 (최신)
├── radar_chart_descriptions.py      레이더 차트 설명
│
├── report_generator.py              리포트 생성 (구버전)
├── genre_profiles.py                장르 프로파일 (미사용)
│
├── test_single_file.py              ⭐ 단일 파일 테스트
├── test_worker.py                   ⭐ 워커 테스트
│
└── README.md                        이 문서
```

---

## 🚀 사용 방법

### 1. 단일 파일 테스트

```bash
cd vocal_analysis
python test_single_file.py
```

**출력:**
- 레이더 차트 점수 (5축)
- 음역대 분석
- 음색 프로파일
- JSON 파일 (`../test_output/test2_result.json`)

### 2. 워커 테스트

```bash
cd vocal_analysis
python test_worker.py
```

**선택 옵션:**
1. 단일 작업 테스트
2. 배치 작업 테스트
3. 둘 다 실행

### 3. Python 코드에서 사용

```python
import sys
sys.path.insert(0, 'vocal_analysis')

from user_vocal_pipeline import UserVocalPipeline

# 파이프라인 초기화
pipeline = UserVocalPipeline()

# 분석 실행
result = pipeline.process("my_acapella.wav")

# 결과 확인
print(result['report']['radar_chart'])
```

---

## 📊 레이더 차트 5축

| 축 | 설명 |
|---|------|
| 🎯 **음정 안정도** | 한 음을 얼마나 흔들림 없이 유지하는가 |
| 🎵 **리듬 안정도** | 자기 템포를 얼마나 일정하게 유지하는가 |
| 📊 **강약 조절** | 소리 크기를 얼마나 자연스럽게 조절하는가 |
| 💎 **발성 선명도** | 소리가 얼마나 또렷하고 깨끗한가 |
| 🎤 **고음 유지력** | 높은 음에서도 안정성이 유지되는가 |

---

## 🔧 모듈 설명

### **user_vocal_pipeline.py** ⭐⭐⭐
**메인 파이프라인**

전체 분석 프로세스를 통합 관리:
1. 오디오 전처리
2. 특징 추출
3. 리포트 생성
4. 임베딩 준비

```python
class UserVocalPipeline:
    def process(audio_path: str) -> Dict
```

---

### **audio_preprocessing.py**
**오디오 전처리**

- 16kHz 리샘플링
- RMS 정규화 (-20dB)
- 무음 제거
- 세그먼트화 (20초, 5초 overlap)

```python
class AudioPreprocessor:
    def preprocess(audio_path: str) -> Tuple[np.ndarray, List[Dict]]
```

---

### **feature_extraction.py**
**특징 추출**

다양한 음향 특징 추출:
- Pitch (F0)
- Energy (RMS)
- Onset (소리 시작점)
- Timbre (음색)
- ECAPA (임베딩)
- Vibrato (비브라토)
- Vocal Technique (발성 기술)

```python
class FeatureExtractor:
    def extract_all_features(audio, segments) -> Dict
```

---

### **report_generator_v2.py**
**리포트 생성 (최신)**

특징을 기반으로 분석 리포트 생성:
- 레이더 차트 (5축)
- 음역대 분석
- 음색 프로파일
- 발성 기술 평가
- 비브라토 분석

```python
class ReportGeneratorV2:
    def generate_report(features: Dict) -> Dict
```

---

### **vocal_analysis_worker.py** ⭐⭐
**프로덕션 워커**

프로덕션 환경용 워커 (현재는 스켈레톤):
- S3에서 오디오 다운로드 (TODO)
- 보컬 분석 실행
- DB에 결과 저장 (TODO)

```python
class VocalAnalysisWorker:
    def process_job(job_id: str) -> Dict
```

---

## 🎯 현재 상태

### ✅ 완료
- [x] 아카펠라 전용 분석 파이프라인
- [x] 레이더 차트 V2 (5축)
- [x] 로컬 파일 테스트
- [x] 워커 스켈레톤

### ⏳ TODO
- [ ] S3 다운로드 구현
- [ ] DB 저장 구현
- [ ] AWS 연동

---

## 📚 참고 문서

- **../CURRENT_STATUS.md** - 현재 상태 요약
- **../SYSTEM_SUMMARY.md** - 시스템 요약
- **../PRODUCTION_DEPLOYMENT_GUIDE.md** - 프로덕션 배포 가이드
- **../VOCAL_ANALYSIS_SYSTEM_DOCUMENTATION.md** - 전체 시스템 문서

---

## 🔄 프로덕션 흐름 (미래)

```
DB (job_id 조회)
  ↓
S3 (오디오 다운로드)
  ↓
vocal_analysis_worker.py
  ↓
user_vocal_pipeline.py (동일한 분석 로직!)
  ↓
DB (결과 저장)
```

**핵심:** `user_vocal_pipeline.py`의 분석 로직은 현재 테스트와 미래 프로덕션에서 동일하게 사용됩니다!

---

## 📝 주의사항

### 경로 설정
- 테스트 파일들은 `vocal_analysis/` 폴더 내에서 실행
- 테스트 데이터는 `../test_data/`에 위치
- 출력은 `../test_output/`에 저장

### Import 경로
```python
# vocal_analysis 폴더 내에서
from user_vocal_pipeline import UserVocalPipeline

# 외부에서
sys.path.insert(0, 'vocal_analysis')
from user_vocal_pipeline import UserVocalPipeline
```

---

**마지막 업데이트:** 2024년 (폴더 구조 정리)


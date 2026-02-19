# 🎤 SINGCHRONIZE 유저 보컬 전처리 파이프라인

유저의 음성 1개 업로드로 **보컬 분석 리포트**와 **노래 추천용 데이터**를 동시에 생성하는 파이프라인입니다.

---

## 📋 목차

1. [개요](#개요)
2. [설치](#설치)
3. [사용법](#사용법)
4. [모듈 설명](#모듈-설명)
5. [출력 형식](#출력-형식)
6. [테스트](#테스트)

---

## 🎯 개요

### 주요 기능

1. **보컬 분석 리포트 생성**
   - 레이더 차트 (5개 품질 지표)
   - 음역대 분석
   - 음색 분석
   - 장르별 적합도 (8개 장르)

2. **노래 추천용 데이터 생성**
   - ECAPA-TDNN 임베딩 (보컬 컬러)
   - 음역대 프로파일
   - 음색 벡터

### 처리 흐름

```
유저 음성 업로드
      ↓
전처리 (표준화 + 세그먼트화)
      ↓
특징 추출 (Pitch, Energy, Onset, Timbre, ECAPA)
      ↓
 ┌────────┴────────┐
 │ 리포트 생성     │ 추천용 임베딩 │
 └─────────────────┘
```

---

## 🔧 설치

### 1. 가상환경 생성 (권장)

```bash
cd ai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 추가 설치 (옵션)

**MR 제거 기능 사용 시:**
```bash
pip install demucs
```

**HNR 계산 (음색 선명도) 사용 시:**
```bash
pip install praat-parselmouth
```

---

## 🚀 사용법

### 기본 사용

```python
from scripts.user_vocal_pipeline import UserVocalPipeline

# 파이프라인 초기화
pipeline = UserVocalPipeline()

# 유저 음성 처리
result = pipeline.process("user_vocal.wav")

# 리포트 출력
print(result['report'])

# 추천용 임베딩
embedding = result['embedding']['representative_embedding']
```

### CLI 사용

```bash
cd scripts

# 기본 실행
python user_vocal_pipeline.py user_vocal.wav

# 출력 디렉토리 지정
python user_vocal_pipeline.py user_vocal.wav -o ./output

# MR 제거 활성화
python user_vocal_pipeline.py user_vocal.wav --remove-mr
```

### 배치 처리

```python
from scripts.user_vocal_pipeline import process_batch

audio_files = ["vocal1.wav", "vocal2.wav", "vocal3.wav"]
results = process_batch(audio_files, output_dir="./output")
```

---

## 📦 모듈 설명

### 1. `audio_preprocessing.py`

**오디오 전처리 모듈**

#### 주요 기능
- **표준화**: Mono 변환, 16kHz 리샘플링, 무음 제거, RMS 정규화
- **세그먼트화**: 20초 window, 5초 hop
- **품질 점수 계산**: 세그먼트별 품질 평가

#### 클래스: `AudioPreprocessor`

```python
preprocessor = AudioPreprocessor(
    target_sr=16000,           # 목표 샘플레이트
    segment_duration=20.0,     # 세그먼트 길이 (초)
    hop_duration=5.0,          # 세그먼트 간격 (초)
    top_db=30                  # 무음 제거 임계값 (dB)
)

audio, segments = preprocessor.preprocess("audio.wav")
```

#### 품질 점수 계산 기준
1. **Voiced ratio** (유성음 비율) - 높을수록 좋음
2. **Clipping** 여부 - 없을수록 좋음
3. **RMS 안정성** - 안정적일수록 좋음
4. **Zero-crossing rate** - 적절한 범위일수록 좋음

---

### 2. `feature_extraction.py`

**특징 추출 모듈**

#### 추출 특징

| 특징 | 설명 | 용도 |
|------|------|------|
| **Pitch (F0)** | 음높이 변화 | 음역대 분석, 음정 안정성 |
| **Energy (RMS)** | 발성 강도 | 호흡 안정성, 소리의 밀도 |
| **Onset** | 소리 시작점 | 리듬 안정성 |
| **Timbre** | 음색 통계 | 음색 프로파일 |
| **ECAPA-TDNN** | 보컬 임베딩 | 추천 엔진 |

#### 클래스: `FeatureExtractor`

```python
extractor = FeatureExtractor(sr=16000)
features = extractor.extract_all_features(audio, segments)
```

#### Pitch (F0) 추출
- **모델**: CREPE (고품질 F0 추출)
- **출력**: F0 contour, voiced mask, 최저/최고음, tessitura

#### Energy (RMS) 추출
- **방법**: librosa RMS
- **출력**: RMS contour, 평균/표준편차, 세그먼트별 통계

#### Onset 추출
- **방법**: librosa onset detection
- **출력**: Onset 시간, IOI (Inter-Onset Interval), 템포 추정

#### Timbre 추출
설명 가능한 5개 음색 축:

| 축 | 특징 | 의미 |
|----|------|------|
| **Brightness** | Spectral Centroid | 고역 성분 (밝기) |
| **Roughness** | Spectral Flatness | 잡음성 (거칠음) |
| **Body** | Low-Mid Band Energy | 저중역 두께 |
| **Clarity** | HNR | 조화 성분 선명도 |
| **Warmth** | Mid-Low Band Energy | 중저역 따뜻함 |

#### ECAPA-TDNN 임베딩
- **모델**: SpeechBrain ECAPA-TDNN
- **차원**: 192-dim
- **방법**: 세그먼트별 임베딩 → 품질 가중 평균

---

### 3. `report_generator.py`

**보컬 분석 리포트 생성 모듈**

#### 클래스: `ReportGenerator`

```python
generator = ReportGenerator()
report = generator.generate_report(features)
```

#### 레이더 차트 (5개 품질 지표)

모든 점수는 **0~100 범위**, 높을수록 좋음

| 지표 | 설명 | 계산 방법 |
|------|------|-----------|
| **음정 안정성** | 음 높이가 얼마나 안정적으로 유지되는가 | F0 표준편차, 급격한 jump 비율 |
| **리듬 안정성** | 템포가 일정하게 유지되는가 | IOI 변동 계수 |
| **호흡 안정성** | 프레이즈를 끊김 없이 이어가는가 | RMS 변동 계수, 에너지 급락 |
| **소리의 밀도** | 발성이 빈약하지 않고 채워지는가 | RMS 안정성, Spectral Flatness |
| **발성의 수준** | 전반적인 발성 컨트롤 품질 | RMS 급변동, Flatness, HNR |

#### 음역대 분석

```python
{
    'lowest_note': 'G2',
    'lowest_hz': 98.0,
    'highest_note': 'D5',
    'highest_hz': 587.3,
    'tessitura_low_note': 'C3',
    'tessitura_high_note': 'A4',
    'range_semitones': 31.2
}
```

- **최저음/최고음**: 실제로 낸 음의 범위
- **테시투라**: 편안하게 자주 사용하는 구간 (25~75 percentile)
- **음역대**: 반음 수로 표현

#### 음색 프로파일

각 축은 **성향**을 나타냄 (좋고 나쁨이 아님)

```python
{
    'brightness': {
        'score': 65.3,
        'description': '밝은 음색'
    },
    'roughness': {
        'score': 32.1,
        'description': '적당히 부드러운 음색'
    },
    ...
}
```

---

### 4. `user_vocal_pipeline.py`

**메인 파이프라인**

#### 클래스: `UserVocalPipeline`

```python
pipeline = UserVocalPipeline(
    sr=16000,                  # 샘플레이트
    segment_duration=20.0,     # 세그먼트 길이
    hop_duration=5.0,          # 세그먼트 간격
    remove_mr_flag=False       # MR 제거 여부
)

result = pipeline.process(
    audio_path="user_vocal.wav",
    output_dir="./output",
    save_features=True
)
```

#### 처리 단계

1. **Step 0**: MR 제거 (선택)
2. **Step 1**: 오디오 전처리
3. **Step 2**: 특징 추출
4. **Step 3**: 보컬 분석 리포트 생성
5. **Step 4**: 추천용 데이터 준비

---

## 📊 출력 형식

### JSON 출력 구조

```json
{
  "report": {
    "radar_chart": {
      "pitch_stability": 78.5,
      "rhythm_consistency": 82.3,
      "breath_control": 71.2,
      "sound_density": 85.6,
      "phonation_quality": 79.8,
      "average": 79.5
    },
    "vocal_range": {
      "lowest_note": "G2",
      "lowest_hz": 98.0,
      "highest_note": "D5",
      "highest_hz": 587.3,
      "tessitura_low_note": "C3",
      "tessitura_high_note": "A4",
      "range_semitones": 31.2
    },
    "timbre_profile": {
      "brightness": {
        "score": 65.3,
        "description": "밝은 음색"
      },
      "roughness": {
        "score": 32.1,
        "description": "적당히 부드러운 음색"
      },
      "body": {
        "score": 58.7,
        "description": "적당한 바디감"
      },
      "clarity": {
        "score": 72.4,
        "description": "선명한 발성"
      },
      "warmth": {
        "score": 61.2,
        "description": "따뜻한 음색"
      }
    }
  },
  "embedding": {
    "representative_embedding": [0.123, -0.456, ...],  // 192-dim
    "embedding_dim": 192,
    "pitch_profile": {
      "f0_min": 98.0,
      "f0_max": 587.3,
      "tessitura_low": 130.8,
      "tessitura_high": 440.0
    },
    "timbre_vector": {
      "brightness": 0.653,
      "roughness": 0.321,
      "body": 0.587,
      "clarity": 0.724,
      "warmth": 0.612
    }
  },
  "metadata": {
    "audio_path": "user_vocal.wav",
    "duration": 45.3,
    "num_segments": 6,
    "sample_rate": 16000
  }
}
```

---

## 🧪 테스트

### 기본 테스트 실행

```bash
cd scripts
python test_pipeline.py
```

이 명령은 다음을 테스트합니다:
1. 오디오 전처리
2. 특징 추출
3. 리포트 생성
4. 전체 파이프라인

### 실제 오디오 파일로 테스트

```bash
python test_pipeline.py your_audio.wav
```

### 개별 모듈 테스트

```python
# 전처리만 테스트
from audio_preprocessing import AudioPreprocessor
preprocessor = AudioPreprocessor()
audio, segments = preprocessor.preprocess("test.wav")

# 특징 추출만 테스트
from feature_extraction import FeatureExtractor
extractor = FeatureExtractor(sr=16000)
features = extractor.extract_pitch(audio, segments)

# 리포트 생성만 테스트
from report_generator import ReportGenerator
generator = ReportGenerator()
report = generator.generate_report(features)
```

---

## 🔄 추천 시스템 연동

### 추천 3단계 전략

```python
# 1단계: ECAPA 유사도로 후보 검색
user_embed = result['embedding']['representative_embedding']
sim_scores = cosine_similarity(user_embed, song_embeds)
top_k_candidates = get_top_k(sim_scores, k=100)

# 2단계: 음역대 필터링
user_range = result['embedding']['pitch_profile']
filtered = filter_by_vocal_range(top_k_candidates, user_range)

# 3단계: 음색 재정렬
user_timbre = result['embedding']['timbre_vector']
final_recommendations = rerank_by_timbre(filtered, user_timbre)
```

### DB 저장 예시

```python
# Supabase 저장
supabase.table("user_vocal_analysis").insert({
    "user_id": user_id,
    "embedding": result['embedding']['representative_embedding'],
    "pitch_profile": result['embedding']['pitch_profile'],
    "timbre_vector": result['embedding']['timbre_vector'],
    "report": result['report'],
    "created_at": datetime.now()
}).execute()
```

---

## 📝 참고사항

### 성능 최적화

1. **ECAPA 임베딩**
   - GPU 사용 권장 (CUDA)
   - 첫 실행 시 모델 다운로드 (약 100MB)
   - ✅ **모델 재사용**: 클래스 변수로 공유하여 모든 인스턴스가 동일한 모델 사용
   - ✅ **메모리 효율성**: 한 번만 로드하여 메모리 절약
   - ✅ **속도 향상**: 두 번째 작업부터 모델 로딩 시간 절약

2. **MR 제거 (Demucs)**
   - 시간 오래 걸림 (30초 음성 → 1~2분)
   - 가능하면 유저에게 아카펠라 업로드 유도

3. **배치 처리**
   - 여러 파일 처리 시 `process_batch()` 사용
   - 모델 재로딩 방지로 속도 향상

### 에러 처리

```python
try:
    result = pipeline.process("user_vocal.wav")
except FileNotFoundError:
    print("파일을 찾을 수 없습니다.")
except Exception as e:
    print(f"처리 실패: {e}")
```

### 지원 포맷

- **입력**: wav, mp3, flac, ogg
- **출력**: JSON, wav (전처리된 오디오)

---

## 🛠️ 개발 로드맵

- [x] 기본 전처리 파이프라인
- [x] 특징 추출 (Pitch, Energy, Onset, Timbre, ECAPA)
- [x] 보컬 분석 리포트 생성
- [x] 추천용 임베딩 생성
- [ ] 장르별 적합도 계산 (곡 DB 구축 후)
- [ ] 실시간 처리 최적화
- [ ] 웹 API 서버 구축
- [ ] 프론트엔드 연동

---

## 📧 문의

문제가 발생하거나 개선 제안이 있으시면 이슈를 등록해주세요.

---

**SINGCHRONIZE** - 당신의 목소리에 맞는 노래를 찾아드립니다 🎤✨

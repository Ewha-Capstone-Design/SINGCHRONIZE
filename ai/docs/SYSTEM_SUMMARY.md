# 🎤 SINGCHRONIZE 보컬 분석 시스템 요약

## 📌 핵심 결정 사항

### ✅ 최종 선택: 아카펠라 전용 + V2 레이더 차트

**이유:**
1. 사용자가 아카펠라로만 녹음 → MR 제거 불필요
2. 처리 속도 빠름 (Demucs 제거)
3. 발성 품질 분석 정확도 향상 (MR 노이즈 없음)

---

## 🎯 레이더 차트 5축 (V2)

### 선택한 축
1. **음정 안정도** (Pitch Stability)
2. **리듬 안정도** (Rhythm Stability)
3. **강약 조절** (Dynamic Control)
4. **발성 선명도** (Vocal Clarity)
5. **고음 유지력** (High Note Stability)

### 선택 이유
- ✅ 각 지표가 명확하고 독립적
- ✅ 측정 방법이 과학적이고 신뢰할 수 있음
- ✅ 사용자가 이해하기 쉽고 개선 방향 파악 용이
- ✅ 실제 보컬 코치들이 사용하는 용어와 유사
- ✅ 아카펠라 녹음에서 완벽하게 측정 가능

### 기각한 축 (원래 버전)
- ❌ 호흡 안정성 (Breath Control) - 측정 방법 모호
- ❌ 소리의 밀도 (Sound Density) - 개념 추상적
- ❌ 발성의 수준 (Phonation Quality) - 너무 포괄적

---

## 📊 각 축별 점수 처리 방법

### 1️⃣ 음정 안정도 (Pitch Stability)

**측정 지표:**
- F0 안정성 (60%) - 각 음표 내 F0 표준편차 (cents)
- 음정 급변 구간 비율 (30%)
- 음 이탈 구간 비율 (10%)

**점수 계산:**
```python
final_score = stability_score * 0.6 + transition_smoothness * 0.3 + voiced_score * 0.1
```

**기준값:**
- F0 std < 20 cents: 90점 이상 (우수)
- F0 std 20~50 cents: 70~90점 (보통)
- F0 std > 50 cents: 70점 미만 (개선 필요)

**성능 향상 장치:**
- 세그먼트별 분석으로 정확도 향상
- Voiced 구간만 필터링하여 노이즈 제거
- Cents 단위 사용으로 음역대 무관 평가

---

### 2️⃣ 리듬 안정도 (Rhythm Stability)

**측정 지표:**
- IOI 변동 계수 (70%)
- Tempo drift (30%) - 선형 회귀로 측정

**점수 계산:**
```python
final_score = ioi_score * 0.7 + drift_score * 0.3
```

**기준값:**
- IOI CV < 0.6: 100점 (매우 안정적)
- IOI CV 0.6~2.0: 100~0점 선형
- IOI CV > 2.0: 0점 (불안정)

**성능 향상 장치:**
- 선형 회귀로 tempo drift 감지
- IOI 변동과 drift를 별도 측정
- Onset 검출 시 에너지 임계값 적용

---

### 3️⃣ 강약 조절 (Dynamic Control)

**측정 지표:**
- 다이나믹 범위 (60%) - dB 단위
- RMS 변화 부드러움 (40%)

**점수 계산:**
```python
final_score = range_score * 0.6 + smoothness_score * 0.4
```

**기준값:**
- Dynamic range > 15dB: 100점 (우수)
- Dynamic range 10~15dB: 67~100점 (보통)
- Dynamic range < 10dB: 67점 미만 (개선 필요)

**성능 향상 장치:**
- 연속형 점수로 binary 문제 해결
- RMS 변화의 부드러움을 별도 측정
- 무음 구간 제거하여 정확도 향상

---

### 4️⃣ 발성 선명도 (Vocal Clarity)

**측정 지표:**
- HNR (40%) - Harmonics-to-Noise Ratio
- Spectral Flatness 역수 (30%)
- Voiced 구간 에너지 안정성 (30%)

**점수 계산:**
```python
final_score = hnr_score * 0.4 + flatness_score * 0.3 + energy_stability_score * 0.3
```

**기준값:**
- HNR > 10dB: 80점 이상 (선명함)
- HNR 5~10dB: 50~80점 (보통)
- HNR < 5dB: 50점 미만 (흐림)

**성능 향상 장치:**
- 프레임 단위 HNR 직접 계산
- Voiced 구간만 필터링
- 다중 지표 조합으로 신뢰도 향상

---

### 5️⃣ 고음 유지력 (High Note Stability)

**측정 지표:**
- 고음 구간 Pitch 안정성 (40%)
- 고음 구간 HNR 유지 (30%)
- 고음 구간 에너지 유지 (30%)

**고음 기준:**
- 개인 최고음의 80% 이상
- 최소 기준: 남성 C4 (261Hz), 여성 F4 (349Hz)

**점수 계산:**
```python
final_score = pitch_stability_score * 0.4 + hnr_score * 0.3 + energy_stability_score * 0.3
```

**기준값:**
- 고음 F0 변화율 < 2%: 80점 이상 (우수)
- 고음 F0 변화율 2~5%: 60~80점 (보통)
- 고음 F0 변화율 > 5%: 60점 미만 (개선 필요)

**성능 향상 장치:**
- 개인별 고음 기준 자동 설정 (공정한 평가)
- 프레임 단위 고음 구간 필터링
- 다중 지표 조합 (Pitch + HNR + Energy)

---

## 🚀 전체 시스템 성능 향상 장치

### 1. 세그먼트 기반 분석
```python
segment_length = 20.0  # 20초
segment_hop = 5.0      # 5초 overlap
```
- 긴 오디오도 안정적으로 처리
- Overlap으로 정보 손실 방지

### 2. Voiced 구간 필터링
```python
voiced_mask = pitch['voiced_mask']
f0_voiced = f0_contour[voiced_mask]
```
- 무음/무성음 제거로 정확도 향상
- 실제 발성 구간만 분석

### 3. 이상치 제거
```python
tessitura_low = np.percentile(f0_voiced, 1)
tessitura_high = np.percentile(f0_voiced, 99)
```
- 극단값 영향 최소화
- 안정적인 통계 계산

### 4. 다중 지표 조합
- 각 축마다 2~3개의 하위 지표 사용
- 가중 평균으로 신뢰도 향상
- 단일 지표의 한계 보완

### 5. 연속형 점수 사용
```python
range_score = (dynamic_range_db / 15) * 100
```
- Binary가 아닌 연속형
- 미세한 차이도 반영
- 점수 분포가 자연스러움

---

## 📈 점수 해석 기준

```python
def get_score_interpretation(score: float) -> str:
    if score >= 90:
        return "매우 우수"
    elif score >= 80:
        return "우수"
    elif score >= 70:
        return "양호"
    elif score >= 60:
        return "보통"
    elif score >= 50:
        return "개선 필요"
    else:
        return "많은 연습 필요"
```

---

## 🎯 측정 가능 vs 불가능

### ✅ 아카펠라에서 측정 가능
- 음정 안정도 (한 음 내 흔들림)
- 리듬 안정도 (자기 템포 일정함)
- 강약 조절
- 발성 선명도
- 고음 유지력
- 음역대
- 음색
- 장르별 적합도

### ❌ 아카펠라에서 측정 불가능
- 음정 정확도 (정답 음정 없음)
- 리듬 정확도 (정답 박자 없음)

---

## 💡 안정도 vs 정확도

### 개념 차이

**안정도 (Stability)**
- 자기 자신과의 비교
- "얼마나 일관되게 유지하는가?"
- 아카펠라에서 측정 가능

**정확도 (Accuracy)**
- 정답과의 비교
- "정답과 얼마나 가까운가?"
- MR 필요 (아카펠라에서 불가능)

### 예시

**음정**
- 안정도: 한 음 내에서 F0 흔들림 정도
- 정확도: 정답 음과의 거리

**리듬**
- 안정도: 자기 템포를 얼마나 일정하게 유지하는가
- 정확도: 정답 박자와 얼마나 가까운가

---

## 🔧 시스템 구조

### 처리 흐름

```
입력: user_acapella.wav
  ↓
[Step 1] 오디오 전처리
  - 16kHz 리샘플링
  - RMS 정규화 (-20dB)
  - 무음 제거
  - 세그먼트화 (20초, 5초 overlap)
  ↓
[Step 2] 특징 추출
  - Pitch (F0, voiced/unvoiced)
  - Energy (RMS contour)
  - Onset (소리 시작점)
  - Timbre (MFCC, Spectral features)
  - ECAPA (음색 임베딩)
  - 음정 정확도 분석 (레이더 차트에 필요)
  - 고급 음색 분석 (MFCC)
  ↓
[Step 3] 리포트 생성
  - 레이더 차트 (5축)
  - 음역대 분석
  - 음색 프로파일
  - 장르별 적합도
  ↓
[Step 4] 임베딩 준비
  - ECAPA 대표 임베딩
  - Pitch 프로파일
  - Timbre 벡터
  ↓
출력: JSON 파일 + 콘솔 요약
```

### 핵심 모듈

| 모듈 | 역할 | 상태 |
|-----|------|------|
| `user_vocal_pipeline.py` | 전체 파이프라인 통합 | ✅ 완료 |
| `audio_preprocessing.py` | 오디오 전처리 | ✅ 완료 |
| `feature_extraction.py` | 특징 추출 | ✅ 완료 |
| `report_generator_v2.py` | 리포트 생성 | ✅ 완료 |
| `radar_chart_descriptions.py` | 레이더 차트 설명 | ✅ 완료 |

---

## 📊 출력 결과 구조

```json
{
  "report": {
    "radar_chart": {
      "pitch_stability": 85.3,
      "rhythm_stability": 78.9,
      "dynamic_control": 72.1,
      "vocal_clarity": 81.5,
      "high_note_stability": 68.2,
      "average": 77.2
    },
    "vocal_range": {
      "lowest_note": "E3",
      "lowest_hz": 164.8,
      "highest_note": "C5",
      "highest_hz": 523.3,
      "tessitura_low_note": "G3",
      "tessitura_high_note": "A4",
      "range_semitones": 20.0
    },
    "timbre_profile": {
      "brightness": {...},
      "roughness": {...},
      "body": {...},
      "clarity": {...},
      "warmth": {...},
      "richness": {...},
      "texture": {...},
      "summary": "밝고 화사한, 따뜻한, 선명한 음색"
    },
    "genre_fitness": {
      "scores": {
        "발라드": 85.3,
        "POP": 78.2,
        "R&B": 72.5,
        ...
      },
      "top_genres": [
        {
          "genre": "발라드",
          "score": 85.3,
          "description": "감성적이고 서정적인 곡",
          "reason": "음역대가 잘 맞음, 음색이 유사함 (밝기, 따뜻함)"
        },
        ...
      ],
      "analysis": {
        "best_match": "발라드",
        "best_score": 85.3,
        "details": {...}
      }
    }
  },
  "embedding": {
    "representative_embedding": [...],  // 192차원
    "embedding_dim": 192,
    "pitch_profile": {
      "f0_min": 164.8,
      "f0_max": 523.3,
      "tessitura_low": 196.0,
      "tessitura_high": 440.0
    },
    "timbre_vector": {
      "brightness": 0.45,
      "roughness": 0.08,
      "body": 0.52,
      "clarity": 0.78,
      "warmth": 0.55
    }
  },
  "metadata": {
    "audio_path": "user_acapella.wav",
    "duration": 45.2,
    "num_segments": 9,
    "sample_rate": 16000
  }
}
```

---

## 🎯 사용 방법

### Python API

```python
from user_vocal_pipeline import UserVocalPipeline

# 파이프라인 초기화
pipeline = UserVocalPipeline()

# 아카펠라 녹음 분석
result = pipeline.process("my_acapella.wav")

# 결과 확인
print(result['report']['radar_chart'])
print(result['report']['vocal_range'])
```

### CLI

```bash
# 기본 사용
python user_vocal_pipeline.py my_acapella.wav

# 출력 디렉토리 지정
python user_vocal_pipeline.py my_acapella.wav -o ./output

# 특징 저장 비활성화
python user_vocal_pipeline.py my_acapella.wav --no-save-features
```

---

## 🆚 기존 시스템과의 차이

### 변경 전 (Hybrid 모드)
- MR + 보컬 녹음
- Demucs로 MR 제거 (시간 오래 걸림)
- 보컬 품질 + 음정/리듬 정확도 측정
- 처리 시간: ~5분 (GPU 기준)

### 변경 후 (아카펠라 전용)
- 아카펠라 녹음만
- MR 제거 불필요
- 보컬 품질 (안정도) 측정
- 처리 시간: ~30초

### 장단점 비교

| 항목 | 기존 (Hybrid) | 현재 (아카펠라) |
|-----|-------------|---------------|
| 처리 속도 | ❌ 느림 | ✅ 빠름 |
| 녹음 편의성 | ✅ MR과 함께 | ❌ 아카펠라만 |
| 음정 정확도 | ✅ 측정 가능 | ❌ 측정 불가 |
| 리듬 정확도 | ✅ 측정 가능 | ❌ 측정 불가 |
| 발성 품질 | ✅ 정확 | ✅ 더 정확 |
| 시스템 복잡도 | ❌ 복잡 | ✅ 단순 |

---

## 🎓 주요 기술 스택

### 오디오 처리
- `librosa` - 오디오 분석
- `scipy` - 신호 처리
- `numpy` - 수치 계산

### 특징 추출
- `librosa.pyin` - F0 추출
- `librosa.onset.onset_detect` - Onset 검출
- `librosa.feature` - MFCC, Spectral features
- ECAPA-TDNN - 음색 임베딩

### 분석 알고리즘
- 선형 회귀 (Tempo drift)
- 표준편차 / 변동계수 (안정성)
- HNR (Harmonics-to-Noise Ratio)
- Spectral Flatness

---

## 📚 참고 문서

1. [ACAPELLA_ONLY_GUIDE.md](./ACAPELLA_ONLY_GUIDE.md) - 아카펠라 전용 가이드
2. [VOCAL_ANALYSIS_SYSTEM_DOCUMENTATION.md](./VOCAL_ANALYSIS_SYSTEM_DOCUMENTATION.md) - 전체 시스템 문서
3. [SEGMENT_NORMALIZATION.md](./docs/SEGMENT_NORMALIZATION.md) - 세그먼트 정규화
4. [RADAR_CHART_EVOLUTION.md](./docs/RADAR_CHART_EVOLUTION.md) - 레이더 차트 진화
5. [STABILITY_VS_ACCURACY.md](./docs/STABILITY_VS_ACCURACY.md) - 안정도 vs 정확도

---

## 🔮 향후 개선 계획

### Phase 1: 현재 (완료)
- ✅ 아카펠라 전용 파이프라인
- ✅ 레이더 차트 5축 (V2)
- ✅ 음역대, 음색 분석
- ✅ 장르별 적합도 계산
- ✅ ECAPA 임베딩

### Phase 2: 추천 시스템 연동
- 🔄 ECAPA 임베딩 기반 유사도 계산
- 🔄 음역대 매칭
- 🔄 음색 유사도 계산
- 🔄 장르별 적합도

### Phase 3: 사용자 피드백
- 📋 점수별 맞춤형 피드백
- 📋 개선 방향 제시
- 📋 연습 방법 추천

### Phase 4: 고급 기능
- 📋 시간에 따른 점수 변화 추적
- 📋 약점 분석 및 맞춤형 연습
- 📋 목표 설정 및 달성 추적

---

## ✅ 최종 결론

### 선택한 방향
**아카펠라 전용 + V2 레이더 차트 (5축)**

### 핵심 이유
1. ✅ **처리 속도**: MR 제거 불필요 → 30초 내 처리
2. ✅ **분석 정확도**: MR 노이즈 없음 → 발성 품질 정확
3. ✅ **시스템 단순화**: 복잡도 감소 → 유지보수 용이
4. ✅ **사용자 이해도**: 직관적인 지표 → 쉬운 해석
5. ✅ **신뢰도**: 과학적 측정 방법 → 높은 신뢰도

### 트레이드오프
- ❌ 음정/리듬 정확도 측정 불가
- ✅ 대신 안정도로 보완 (일관성 측정)
- ✅ 사용자는 아카펠라 녹음만 하면 됨

### 추천 사유
**V2 레이더 차트**가 원래 버전보다 우수한 이유:
1. 각 지표가 명확하고 독립적
2. 측정 방법이 과학적
3. 사용자 친화적
4. 실전 적용성 높음
5. 아카펠라에서 완벽하게 측정 가능

---

**최종 권장: V2 레이더 차트 (아카펠라 전용) 사용** ✅


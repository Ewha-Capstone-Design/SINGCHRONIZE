# 🧪 테스트 실행 가이드

## 📋 test1.m4a 파일로 테스트하기

### 방법 1: 간단한 스크립트 실행 (추천) ⭐

```bash
cd /Users/dldbstj/SINGCHRONIZE-1/ai
python3 test_single_file.py
```

---

### 방법 2: 직접 실행

```bash
cd /Users/dldbstj/SINGCHRONIZE-1/ai/scripts
python3 user_vocal_pipeline.py ../test_data/test1.m4a -o ../test_output
```

---

### 방법 3: Python 인터프리터에서 실행

```bash
cd /Users/dldbstj/SINGCHRONIZE-1/ai
python3
```

```python
# Python 인터프리터에서
import sys
sys.path.insert(0, 'scripts')

from user_vocal_pipeline import UserVocalPipeline

pipeline = UserVocalPipeline()
result = pipeline.process('test_data/test1.m4a', 'test_output')

# 결과 확인
print(result['report']['radar_chart'])
print(result['report']['timbre_profile']['summary'])
```

---

## 📊 예상 출력

### 터미널 출력

```
============================================================
🎤 SINGCHRONIZE 보컬 분석 테스트
============================================================

📁 입력 파일: test_data/test1.m4a
📁 출력 폴더: test_output

============================================================
🎵 보컬 분리 시작 (Demucs)
============================================================
ℹ️  아카펠라 입력 시 → 아카펠라 그대로 출력
ℹ️  MR 포함 입력 시 → 보컬만 분리하여 출력
============================================================
✓ Demucs 모델 로드 완료 (device: cpu)
✓ 오디오 로드: test_data/test1.m4a
⏳ 보컬 분리 중... (수 분 소요)
✓ 보컬 분리 완료: test_output/vocals/test1_vocals.wav

[Step 1] 오디오 전처리
✓ 오디오 로드: test_output/vocals/test1_vocals.wav
  - 원본 샘플레이트: 44100Hz
  - 원본 길이: 45.23초
✓ 표준화 완료
  - Mono 변환
  - 리샘플링: 16000Hz
  - 무음 제거
  - RMS 정규화
✓ 세그먼트 생성 완료
  - 세그먼트 개수: 6개
  - 평균 품질: 0.85

[Step 2] 특징 추출
✓ F0 추출 완료
  - 음역대: 196.0Hz ~ 587.3Hz
  - 테시투라: 261.6Hz ~ 440.0Hz
✓ RMS 추출 완료
✓ Onset 추출 완료
✓ Timbre 추출 완료
✓ ECAPA 임베딩 추출 완료

[Step 3] 리포트 생성
✓ 레이더 차트 계산 완료
✓ 음역대 분석 완료
✓ 음색 프로파일 생성 완료
✓ 장르별 적합도 계산 완료

============================================================
📊 보컬 분석 결과
============================================================

[레이더 차트]
  • 음정 안정성: 78.5/100
  • 리듬 안정성: 82.3/100
  • 호흡 안정성: 71.2/100
  • 소리의 밀도: 85.6/100
  • 발성의 수준: 79.8/100
  • 평균: 79.5/100

[음역대 분석]
  최저음: G2 (98.0 Hz)
  최고음: D5 (587.3 Hz)
  테시투라: C3 (130.8 Hz) ~ A4 (440.0 Hz)
  음역대: 31.2 반음 (약 2.6 옥타브)

[음색 프로파일]
  📝 전체 요약: 밝고 화사한, 따뜻한, 선명한 음색

  ✨ brightness (밝은 편)
     → 고역이 적당히 살아있어 밝은 편
  🌊 roughness (부드러움)
     → 적당히 부드럽고 정돈된 질감
  💪 body (적당함)
     → 저중역이 적당히 받쳐주는 편
  💎 clarity (매우 선명)
     → 조화 성분이 뚜렷해 선명하고 또렷한 발성
  🔥 warmth (따뜻한 편)
     → 중저역이 적당히 있어 따뜻한 편

[장르별 적합도]
   1. 발라드     ████████████████████ 85.3점
   2. POP       ███████████████░░░░░ 78.2점
   3. R&B       ██████████████░░░░░░ 72.1점
   4. 댄스       █████████████░░░░░░░ 68.5점
   5. 인디       ████████████░░░░░░░░ 65.7점
   6. JPOP      ████████████░░░░░░░░ 62.3점
   7. 트로트      ███████████░░░░░░░░░ 58.9점
   8. 락/메탈     ████████░░░░░░░░░░░░ 45.2점

[TOP 3 상세 분석]
  1. 발라드: 85.3점
     → 음역대가 잘 맞음, 음색이 유사함
  2. POP: 78.2점
     → 발성 스타일이 적합함
  3. R&B: 72.1점
     → 전반적으로 적합함

============================================================
✅ 테스트 완료!
============================================================

📊 결과 파일: test_output/test1_result.json
```

---

## 📁 생성되는 파일

### 1. `test_output/test1_result.json`
전체 분석 결과 (JSON)

### 2. `test_output/vocals/test1_vocals.wav`
Demucs로 분리된 보컬 (WAV)

### 3. `test_output/test1_preprocessed.wav` (선택)
전처리된 오디오 (save_features=True 시)

---

## 🔍 결과 확인

### JSON 파일 예쁘게 보기

```bash
cat test_output/test1_result.json | python3 -m json.tool
```

### 특정 필드만 확인

```bash
# 레이더 차트
cat test_output/test1_result.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(json.dumps(data['report']['radar_chart'], indent=2))
"

# 음색 요약
cat test_output/test1_result.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data['report']['timbre_profile']['summary'])
"

# 장르 점수
cat test_output/test1_result.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(json.dumps(data['report']['genre_fitness']['scores'], indent=2))
"
```

---

## ⏱️ 예상 소요 시간

| 단계 | CPU | GPU |
|------|-----|-----|
| Demucs 보컬 분리 | ~2분 | ~10초 |
| 전처리 | ~1초 | ~1초 |
| 특징 추출 | ~5초 | ~5초 |
| 리포트 생성 | ~1초 | ~1초 |
| **전체** | **~2분 10초** | **~20초** |

---

## ⚠️ 주의사항

### 1. 첫 실행 시 모델 다운로드
- **Demucs**: ~330MB
- **ECAPA-TDNN**: ~80MB
- **CREPE**: ~90MB

**총 ~500MB 다운로드 (첫 실행 시만)**

### 2. 메모리 사용
- **최소**: 2GB RAM
- **권장**: 4GB RAM

### 3. ffmpeg 필요
```bash
# macOS
brew install ffmpeg

# 설치 확인
ffmpeg -version
```

---

## 🐛 문제 해결

### 에러: "command not found: python"
```bash
# python3 사용
python3 test_single_file.py
```

### 에러: "No module named 'librosa'"
```bash
# 패키지 설치
pip3 install -r requirements.txt
```

### 에러: "ffmpeg not found"
```bash
# ffmpeg 설치
brew install ffmpeg
```

### 에러: "CUDA out of memory"
```bash
# CPU 모드로 실행 (자동)
# GPU 메모리 부족 시 자동으로 CPU 사용
```

---

## 🎯 빠른 시작

```bash
# 1. 디렉토리 이동
cd /Users/dldbstj/SINGCHRONIZE-1/ai

# 2. 테스트 실행
python3 test_single_file.py

# 3. 결과 확인
cat test_output/test1_result.json | python3 -m json.tool | head -50
```

**끝!** 🎤✨



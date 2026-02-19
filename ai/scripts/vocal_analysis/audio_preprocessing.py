"""
오디오 전처리 모듈
- 유저 음성 표준화
- 세그먼트화
- 품질 점수 계산
"""
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import Tuple, List, Dict
import warnings
warnings.filterwarnings('ignore')


class AudioPreprocessor:
    """
    오디오 전처리 클래스
    
    주요 기능:
    1. 오디오 표준화 (mono, 16kHz, 정규화)
    2. 무음 제거
    3. 세그먼트화 (20초 window, 5초 hop)
    4. 세그먼트별 품질 점수 계산
    """
    
    def __init__(
        self,
        target_sr: int = 16000,
        segment_duration: float = 20.0,  # 20초
        hop_duration: float = 5.0,        # 5초
        top_db: int = 30,                 # 무음 제거 임계값
        normalize_segments: bool = True,  # 세그먼트별 정규화 여부
    ):
        """
        Args:
            target_sr: 목표 샘플레이트 (16kHz - 음성 분석에 적합)
            segment_duration: 세그먼트 길이 (초)
            hop_duration: 세그먼트 간격 (초)
            top_db: 무음 판단 임계값 (dB)
            normalize_segments: 세그먼트별 정규화 여부 (기본: True)
        """
        self.target_sr = target_sr
        self.segment_duration = segment_duration
        self.hop_duration = hop_duration
        self.top_db = top_db
        self.normalize_segments = normalize_segments
        
        # 샘플 단위로 변환
        self.segment_samples = int(segment_duration * target_sr)
        self.hop_samples = int(hop_duration * target_sr)
    
    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        오디오 파일 로드
        
        Args:
            audio_path: 오디오 파일 경로 (wav, mp3 등)
        
        Returns:
            audio: 오디오 신호 (numpy array)
            sr: 샘플레이트
        """
        audio, sr = librosa.load(audio_path, sr=None, mono=False)
        print(f"✓ 오디오 로드: {audio_path}")
        print(f"  - 원본 샘플레이트: {sr}Hz")
        print(f"  - 원본 길이: {len(audio) / sr:.2f}초")
        return audio, sr
    
    def standardize(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        오디오 표준화
        
        1. Mono 변환 (스테레오 → 모노)
        2. 16kHz 리샘플링
        3. 앞뒤 무음 제거
        4. RMS 정규화 (-20dB)
        
        Args:
            audio: 입력 오디오
            sr: 샘플레이트
        
        Returns:
            표준화된 오디오
        """
        # 1. Mono 변환
        if audio.ndim > 1:
            audio = librosa.to_mono(audio)
            print("✓ Mono 변환 완료")
        
        # 2. 리샘플링
        if sr != self.target_sr:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=self.target_sr)
            print(f"✓ 리샘플링 완료: {sr}Hz → {self.target_sr}Hz")
        
        # 3. 무음 제거 (앞뒤)
        audio_trimmed, _ = librosa.effects.trim(audio, top_db=self.top_db)
        removed_duration = (len(audio) - len(audio_trimmed)) / self.target_sr
        print(f"✓ 무음 제거: {removed_duration:.2f}초 제거됨")
        
        # 4. RMS 정규화 (-20dB)
        target_rms_db = -20.0
        current_rms = np.sqrt(np.mean(audio_trimmed ** 2))
        target_rms = 10 ** (target_rms_db / 20)
        
        if current_rms > 0:
            audio_normalized = audio_trimmed * (target_rms / current_rms)
        else:
            audio_normalized = audio_trimmed
        
        print(f"✓ RMS 정규화 완료: {target_rms_db}dB")
        print(f"✓ 최종 길이: {len(audio_normalized) / self.target_sr:.2f}초")
        
        return audio_normalized
    
    def create_segments(self, audio: np.ndarray) -> List[Dict]:
        """
        오디오를 세그먼트로 분할
        
        20초 window, 5초 hop으로 슬라이딩 윈도우 적용
        각 세그먼트에 품질 점수 계산
        
        Args:
            audio: 표준화된 오디오
        
        Returns:
            세그먼트 리스트 [
                {
                    'audio': 세그먼트 오디오,
                    'start_time': 시작 시간(초),
                    'end_time': 종료 시간(초),
                    'quality_score': 품질 점수 (0~1)
                },
                ...
            ]
        """
        segments = []
        total_samples = len(audio)
        
        # 슬라이딩 윈도우
        for start in range(0, total_samples - self.segment_samples + 1, self.hop_samples):
            end = start + self.segment_samples
            segment_audio = audio[start:end]
            
            # 세그먼트별 정규화 (옵션)
            if self.normalize_segments:
                segment_audio = self._normalize_segment(segment_audio)
            
            # 시간 정보
            start_time = start / self.target_sr
            end_time = end / self.target_sr
            
            # 품질 점수 계산
            quality = self._calculate_segment_quality(segment_audio)
            
            segments.append({
                'audio': segment_audio,
                'start_time': start_time,
                'end_time': end_time,
                'quality_score': quality
            })
        
        # 마지막 세그먼트 (남은 부분)
        if total_samples % self.hop_samples != 0:
            remaining_start = len(segments) * self.hop_samples
            if remaining_start < total_samples:
                segment_audio = audio[remaining_start:]
                
                # 패딩 (20초 미만이면)
                if len(segment_audio) < self.segment_samples:
                    segment_audio = np.pad(
                        segment_audio,
                        (0, self.segment_samples - len(segment_audio)),
                        mode='constant'
                    )
                
                # 세그먼트별 정규화 (옵션)
                if self.normalize_segments:
                    segment_audio = self._normalize_segment(segment_audio)
                
                start_time = remaining_start / self.target_sr
                end_time = total_samples / self.target_sr
                quality = self._calculate_segment_quality(segment_audio)
                
                segments.append({
                    'audio': segment_audio,
                    'start_time': start_time,
                    'end_time': end_time,
                    'quality_score': quality
                })
        
        print(f"\n✓ 세그먼트 생성 완료: {len(segments)}개")
        print(f"  - 평균 품질 점수: {np.mean([s['quality_score'] for s in segments]):.3f}")
        
        return segments
    
    def _normalize_segment(self, segment: np.ndarray) -> np.ndarray:
        """
        세그먼트별 정규화
        
        각 세그먼트를 독립적으로 정규화하여 볼륨 차이를 제거
        
        방법:
        1. Peak Normalization (최대값 기준)
        2. RMS Normalization (에너지 기준)
        
        현재는 RMS Normalization 사용
        
        Args:
            segment: 세그먼트 오디오
        
        Returns:
            정규화된 세그먼트
        """
        # RMS 계산
        rms = np.sqrt(np.mean(segment ** 2))
        
        # 무음 구간 체크
        if rms < 1e-6:  # 거의 무음
            return segment
        
        # 목표 RMS (전체 오디오와 동일한 -20dB)
        target_rms = 10 ** (-20.0 / 20)
        
        # 정규화
        normalized = segment * (target_rms / rms)
        
        # 클리핑 방지 (±1.0 초과 방지)
        max_val = np.max(np.abs(normalized))
        if max_val > 0.99:
            normalized = normalized * (0.99 / max_val)
        
        return normalized
    
    def _calculate_segment_quality(self, segment: np.ndarray) -> float:
        """
        세그먼트 품질 점수 계산
        
        품질 기준:
        1. Voiced ratio (유성음 비율) - 높을수록 좋음
        2. Clipping 여부 - 없을수록 좋음
        3. RMS 안정성 - 안정적일수록 좋음
        4. Zero-crossing rate - 적절한 범위일수록 좋음
        
        Args:
            segment: 세그먼트 오디오
        
        Returns:
            품질 점수 (0~1, 높을수록 좋음)
        """
        scores = []
        
        # 1. Voiced ratio (에너지 기반 간단 추정)
        frame_length = 2048
        hop_length = 512
        rms = librosa.feature.rms(y=segment, frame_length=frame_length, hop_length=hop_length)[0]
        rms_threshold = np.percentile(rms, 30)  # 하위 30% 기준
        voiced_ratio = np.sum(rms > rms_threshold) / len(rms)
        scores.append(voiced_ratio)
        
        # 2. Clipping 체크 (0.99 이상 값의 비율)
        clipping_ratio = np.sum(np.abs(segment) > 0.99) / len(segment)
        clipping_score = 1.0 - min(clipping_ratio * 10, 1.0)  # 10% 이상이면 0점
        scores.append(clipping_score)
        
        # 3. RMS 안정성 (변동 계수)
        if np.mean(rms) > 0:
            rms_cv = np.std(rms) / np.mean(rms)
            rms_stability = 1.0 / (1.0 + rms_cv)  # 변동이 적을수록 높은 점수
        else:
            rms_stability = 0.0
        scores.append(rms_stability)
        
        # 4. Zero-crossing rate (적절한 범위: 0.05 ~ 0.15)
        zcr = librosa.feature.zero_crossing_rate(segment, frame_length=frame_length, hop_length=hop_length)[0]
        mean_zcr = np.mean(zcr)
        if 0.05 <= mean_zcr <= 0.15:
            zcr_score = 1.0
        else:
            zcr_score = max(0.0, 1.0 - abs(mean_zcr - 0.1) * 5)
        scores.append(zcr_score)
        
        # 가중 평균 (voiced ratio가 가장 중요)
        weights = [0.4, 0.3, 0.2, 0.1]
        quality = np.average(scores, weights=weights)
        
        return float(quality)
    
    def preprocess(self, audio_path: str, output_dir: str = None) -> Tuple[np.ndarray, List[Dict]]:
        """
        전체 전처리 파이프라인 실행
        
        Args:
            audio_path: 입력 오디오 파일 경로
            output_dir: 전처리된 오디오 저장 디렉토리 (선택)
        
        Returns:
            audio: 표준화된 전체 오디오
            segments: 세그먼트 리스트
        """
        print("\n" + "="*60)
        print("🎤 오디오 전처리 시작")
        print("="*60)
        
        # 1. 로드
        audio, sr = self.load_audio(audio_path)
        
        # 2. 표준화
        print("\n[표준화 처리]")
        audio_std = self.standardize(audio, sr)
        
        # 3. 세그먼트화
        print("\n[세그먼트 생성]")
        segments = self.create_segments(audio_std)
        
        # 4. 저장 (선택)
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 전체 오디오 저장
            output_file = output_path / f"{Path(audio_path).stem}_preprocessed.wav"
            sf.write(output_file, audio_std, self.target_sr)
            print(f"\n✓ 전처리 오디오 저장: {output_file}")
        
        print("\n" + "="*60)
        print("✅ 전처리 완료!")
        print("="*60 + "\n")
        
        return audio_std, segments


def remove_mr(audio_path: str, output_dir: str = None) -> str:
    """
    MR 제거 (보컬 분리)
    
    Demucs를 사용하여 vocals만 추출
    
    Args:
        audio_path: 입력 오디오 경로
        output_dir: 출력 디렉토리
    
    Returns:
        vocals_path: 추출된 보컬 파일 경로
    
    Note:
        - 이 함수는 시간이 오래 걸림 (GPU 권장)
        - MR 포함 여부와 무관하게 사용 가능
        - 아카펠라 입력 시 → 아카펠라 그대로 출력 (안전)
        - MR 포함 입력 시 → 보컬만 분리하여 출력
    """
    try:
        import torch
        import torchaudio
        from demucs.pretrained import get_model
        from demucs.apply import apply_model
        
        print("\n" + "="*60)
        print("🎵 보컬 분리 시작 (Demucs)")
        print("="*60)
        print("ℹ️  아카펠라 입력 시 → 아카펠라 그대로 출력")
        print("ℹ️  MR 포함 입력 시 → 보컬만 분리하여 출력")
        print("="*60)
        
        # 모델 로드
        model = get_model('htdemucs')
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model.to(device)
        print(f"✓ Demucs 모델 로드 완료 (device: {device})")
        
        # 오디오 로드
        wav, sr = torchaudio.load(audio_path)
        wav = wav.to(device)
        print(f"✓ 오디오 로드: {audio_path}")
        
        # 보컬 분리
        print("⏳ 보컬 분리 중... (수 분 소요)")
        with torch.no_grad():
            sources = apply_model(model, wav[None], device=device)[0]
        
        # vocals 추출 (sources: [drums, bass, other, vocals])
        vocals = sources[3]  # vocals
        
        # 저장
        if output_dir is None:
            output_dir = Path(audio_path).parent / "vocals"
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        vocals_file = output_path / f"{Path(audio_path).stem}_vocals.wav"
        torchaudio.save(vocals_file, vocals.cpu(), sr)
        
        print(f"✓ 보컬 저장: {vocals_file}")
        print("="*60 + "\n")
        
        return str(vocals_file)
    
    except ImportError:
        print("⚠️  Demucs가 설치되지 않았습니다.")
        print("   pip install demucs 로 설치해주세요.")
        return audio_path
    except Exception as e:
        print(f"❌ MR 제거 실패: {e}")
        return audio_path


# 테스트용
if __name__ == "__main__":
    # 예시 사용법
    preprocessor = AudioPreprocessor(
        target_sr=16000,
        segment_duration=20.0,
        hop_duration=5.0
    )
    
    # 테스트 오디오 경로 (실제 파일로 교체 필요)
    test_audio = "test_vocal.wav"
    
    if Path(test_audio).exists():
        audio, segments = preprocessor.preprocess(
            audio_path=test_audio,
            output_dir="./output"
        )
        
        print(f"전체 오디오 shape: {audio.shape}")
        print(f"세그먼트 개수: {len(segments)}")
        print(f"첫 세그먼트 품질: {segments[0]['quality_score']:.3f}")
    else:
        print(f"테스트 파일이 없습니다: {test_audio}")


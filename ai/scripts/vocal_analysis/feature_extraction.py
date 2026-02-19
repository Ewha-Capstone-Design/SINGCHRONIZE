"""
특징 추출 모듈
- Pitch (F0) 추출
- Energy (RMS) 추출
- Onset 추출
- Timbre Features 추출
- ECAPA-TDNN 임베딩 추출
- 고급 보컬 분석 (음정 정확도, 비브라토, 발성 기술)
"""
import numpy as np
import librosa
# import crepe  # 빌드 문제로 librosa.pyin 사용
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# 고급 보컬 분석 모듈
from advanced_vocal_analysis import AdvancedVocalAnalyzer


class FeatureExtractor:
    """
    오디오 특징 추출 클래스
    
    추출 특징:
    1. Pitch (F0) - 음높이
    2. Energy (RMS) - 발성 강도
    3. Onset - 소리 시작점
    4. Timbre - 음색 (Spectral Centroid, Flatness, Band Energy, HNR)
    5. ECAPA-TDNN 임베딩 - 보컬 컬러
    
    설계:
    - ECAPA-TDNN 모델은 클래스 변수로 저장하여 모든 인스턴스가 공유합니다.
    - 이는 메모리 효율성과 성능 최적화를 위한 설계입니다.
    - 모델은 stateless하므로 동시 사용에 문제가 없습니다.
    """
    
    # ECAPA-TDNN 모델을 클래스 변수로 저장 (모든 인스턴스가 공유)
    # 프로덕션 환경에서도 동일하게 적용: 메모리 효율성 및 성능 최적화
    _ecapa_classifier = None
    _ecapa_model_loaded = False
    
    def __init__(self, sr: int = 16000):
        """
        Args:
            sr: 샘플레이트 (16kHz 권장)
        """
        self.sr = sr
        
        # 고급 보컬 분석기
        self.advanced_analyzer = AdvancedVocalAnalyzer(sr=sr)
    
    def extract_all_features(
        self,
        audio: np.ndarray,
        segments: List[Dict]
    ) -> Dict:
        """
        모든 특징을 한 번에 추출
        
        Args:
            audio: 전체 오디오 (표준화된)
            segments: 세그먼트 리스트
        
        Returns:
            features: {
                'pitch': {...},
                'energy': {...},
                'onset': {...},
                'timbre': {...},
                'embedding': {...},
                'pitch_accuracy': {...},  # 레이더 차트에 필요
                'advanced_timbre': {...}  # 음색 프로파일에 필요
            }
        """
        print("\n" + "="*60)
        print("🎵 특징 추출 시작")
        print("="*60)
        
        features = {}
        
        # 1. Pitch (F0)
        print("\n[1/6] Pitch (F0) 추출 중...")
        features['pitch'] = self.extract_pitch(audio, segments)
        
        # 2. Energy (RMS)
        print("\n[2/6] Energy (RMS) 추출 중...")
        features['energy'] = self.extract_energy(audio, segments)
        
        # 3. Onset
        print("\n[3/6] Onset 추출 중...")
        features['onset'] = self.extract_onset(audio)
        
        # 4. Timbre
        print("\n[4/6] Timbre 추출 중...")
        features['timbre'] = self.extract_timbre(audio, segments)
        
        # 5. ECAPA Embedding
        print("\n[5/6] ECAPA 임베딩 추출 중...")
        # 속도 최적화: 최대 5개 세그먼트 사용 (품질 상위 + 시간 분포 고려)
        # 5개는 정확도와 속도의 좋은 균형점 (3개는 너무 적고, 7개 이상은 느림)
        features['embedding'] = self.extract_ecapa_embedding(segments, max_segments=5)
        
        # 6. 음정 정확도 분석 (레이더 차트에 필요)
        print("\n[6/6] 음정 정확도 분석 중...")
        features['pitch_accuracy'] = self.advanced_analyzer.analyze_pitch_accuracy(
            np.array(features['pitch']['f0_contour']),
            np.array(features['pitch']['voiced_mask']),
            features['pitch']['time']
        )
        
        # 고급 음색 분석 (MFCC) - 음색 프로파일에 필요
        features['advanced_timbre'] = self.advanced_analyzer.analyze_advanced_timbre(audio)
        
        print("\n" + "="*60)
        print("✅ 특징 추출 완료!")
        print("="*60 + "\n")
        
        return features
    
    # ========================================
    # 1. Pitch (F0) 추출
    # ========================================
    
    def extract_pitch(
        self,
        audio: np.ndarray,
        segments: List[Dict]
    ) -> Dict:
        """
        Pitch (F0) 추출
        
        librosa pyin 사용 (F0 추출)
        
        추출 정보:
        - f0_contour: 전체 F0 변화 곡선
        - voiced_mask: 유성음 구간 마스크
        - f0_min: 최저 음높이 (Hz)
        - f0_max: 최고 음높이 (Hz)
        - tessitura: 편안 구간 (25~75 percentile)
        - segment_stats: 세그먼트별 통계
        
        Args:
            audio: 전체 오디오
            segments: 세그먼트 리스트
        
        Returns:
            pitch_features: Dict
        """
        # librosa pyin으로 F0 추출
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz('C2'),  # 65 Hz
            fmax=librosa.note_to_hz('C7'),  # 2093 Hz
            sr=self.sr,
            frame_length=2048,
            hop_length=160  # ~10ms at 16kHz
        )
        
        # NaN 제거 및 voiced mask
        # threshold 낮춤: 0.5 → 0.1 (더 많은 유성음 감지)
        voiced_mask = ~np.isnan(f0) & (voiced_probs > 0.1)
        frequency = np.nan_to_num(f0, nan=0.0)
        f0_voiced = frequency[voiced_mask]
        
        # time 생성
        time = librosa.frames_to_time(
            np.arange(len(frequency)),
            sr=self.sr,
            hop_length=160
        )
        
        # 전체 통계
        if len(f0_voiced) > 0:
            f0_min = float(np.min(f0_voiced))
            f0_max = float(np.max(f0_voiced))
            f0_mean = float(np.mean(f0_voiced))
            f0_std = float(np.std(f0_voiced))
            
            # Tessitura (25~75 percentile)
            tessitura_low = float(np.percentile(f0_voiced, 25))
            tessitura_high = float(np.percentile(f0_voiced, 75))
        else:
            f0_min = f0_max = f0_mean = f0_std = 0.0
            tessitura_low = tessitura_high = 0.0
        
        # 세그먼트별 통계
        segment_stats = []
        for seg in segments:
            seg_audio = seg['audio']
            
            # 세그먼트 F0 추출 (librosa pyin)
            seg_f0, seg_voiced_flag, seg_voiced_probs = librosa.pyin(
                seg_audio,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'),
                sr=self.sr,
                frame_length=2048,
                hop_length=160
            )
            
            # threshold 낮춤: 0.5 → 0.1
            seg_voiced = ~np.isnan(seg_f0) & (seg_voiced_probs > 0.1)
            seg_f0 = seg_f0[seg_voiced]
            
            if len(seg_f0) > 0:
                segment_stats.append({
                    'start_time': seg['start_time'],
                    'end_time': seg['end_time'],
                    'f0_mean': float(np.mean(seg_f0)),
                    'f0_std': float(np.std(seg_f0)),
                    'f0_min': float(np.min(seg_f0)),
                    'f0_max': float(np.max(seg_f0)),
                    'voiced_ratio': float(np.sum(seg_voiced) / len(seg_voiced))
                })
            else:
                segment_stats.append({
                    'start_time': seg['start_time'],
                    'end_time': seg['end_time'],
                    'f0_mean': 0.0,
                    'f0_std': 0.0,
                    'f0_min': 0.0,
                    'f0_max': 0.0,
                    'voiced_ratio': 0.0
                })
        
        print(f"✓ F0 추출 완료")
        print(f"  - 음역대: {f0_min:.1f}Hz ~ {f0_max:.1f}Hz")
        print(f"  - 테시투라: {tessitura_low:.1f}Hz ~ {tessitura_high:.1f}Hz")
        print(f"  - 평균 F0: {f0_mean:.1f}Hz (±{f0_std:.1f})")
        
        return {
            'f0_contour': frequency.tolist(),
            'time': time.tolist(),
            'confidence': voiced_probs.tolist(),  # pyin의 voiced_probs 사용
            'voiced_mask': voiced_mask.tolist(),
            'f0_min': f0_min,
            'f0_max': f0_max,
            'f0_mean': f0_mean,
            'f0_std': f0_std,
            'tessitura_low': tessitura_low,
            'tessitura_high': tessitura_high,
            'segment_stats': segment_stats
        }
    
    # ========================================
    # 2. Energy (RMS) 추출
    # ========================================
    
    def extract_energy(
        self,
        audio: np.ndarray,
        segments: List[Dict]
    ) -> Dict:
        """
        Energy (RMS) 추출
        
        발성 강도를 나타내는 RMS (Root Mean Square) 추출
        
        추출 정보:
        - rms_contour: 전체 RMS 변화 곡선
        - rms_mean: 평균 RMS
        - rms_std: RMS 표준편차
        - segment_stats: 세그먼트별 통계
        
        Args:
            audio: 전체 오디오
            segments: 세그먼트 리스트
        
        Returns:
            energy_features: Dict
        """
        # 전체 RMS
        frame_length = 2048
        hop_length = 512
        
        rms = librosa.feature.rms(
            y=audio,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]
        
        # 통계
        rms_mean = float(np.mean(rms))
        rms_std = float(np.std(rms))
        rms_max = float(np.max(rms))
        
        # 세그먼트별 통계
        segment_stats = []
        for seg in segments:
            seg_rms = librosa.feature.rms(
                y=seg['audio'],
                frame_length=frame_length,
                hop_length=hop_length
            )[0]
            
            segment_stats.append({
                'start_time': seg['start_time'],
                'end_time': seg['end_time'],
                'rms_mean': float(np.mean(seg_rms)),
                'rms_std': float(np.std(seg_rms)),
                'rms_max': float(np.max(seg_rms)),
                'rms_cv': float(np.std(seg_rms) / np.mean(seg_rms)) if np.mean(seg_rms) > 0 else 0.0
            })
        
        print(f"✓ RMS 추출 완료")
        print(f"  - 평균 RMS: {rms_mean:.4f} (±{rms_std:.4f})")
        print(f"  - 최대 RMS: {rms_max:.4f}")
        
        return {
            'rms_contour': rms.tolist(),
            'rms_mean': rms_mean,
            'rms_std': rms_std,
            'rms_max': rms_max,
            'segment_stats': segment_stats
        }
    
    # ========================================
    # 3. Onset 추출
    # ========================================
    
    def extract_onset(self, audio: np.ndarray) -> Dict:
        """
        Onset 추출
        
        소리 시작점을 감지하여 리듬 분석에 사용
        
        추출 정보:
        - onset_times: 시작점 시간 리스트 (초)
        - onset_intervals: 시작점 간격 (IOI: Inter-Onset Interval)
        - tempo_estimate: 추정 템포 (BPM)
        
        Args:
            audio: 전체 오디오
        
        Returns:
            onset_features: Dict
        """
        # Onset 감지
        hop_length = 512
        onset_frames = librosa.onset.onset_detect(
            y=audio,
            sr=self.sr,
            hop_length=hop_length,
            backtrack=True
        )
        
        # 프레임 → 시간 변환
        onset_times = librosa.frames_to_time(onset_frames, sr=self.sr, hop_length=hop_length)
        
        # Onset 간격 (IOI)
        if len(onset_times) > 1:
            onset_intervals = np.diff(onset_times)
            ioi_mean = float(np.mean(onset_intervals))
            ioi_std = float(np.std(onset_intervals))
            ioi_cv = float(ioi_std / ioi_mean) if ioi_mean > 0 else 0.0
            
            # 템포 추정 (평균 IOI 기반)
            tempo_estimate = 60.0 / ioi_mean if ioi_mean > 0 else 0.0
        else:
            onset_intervals = []
            ioi_mean = ioi_std = ioi_cv = tempo_estimate = 0.0
        
        print(f"✓ Onset 추출 완료")
        print(f"  - Onset 개수: {len(onset_times)}")
        print(f"  - 평균 IOI: {ioi_mean:.3f}초 (±{ioi_std:.3f})")
        print(f"  - 추정 템포: {tempo_estimate:.1f} BPM")
        
        return {
            'onset_times': onset_times.tolist(),
            'onset_intervals': onset_intervals.tolist() if len(onset_intervals) > 0 else [],
            'ioi_mean': ioi_mean,
            'ioi_std': ioi_std,
            'ioi_cv': ioi_cv,
            'tempo_estimate': tempo_estimate
        }
    
    # ========================================
    # 4. Timbre 추출
    # ========================================
    
    def extract_timbre(
        self,
        audio: np.ndarray,
        segments: List[Dict]
    ) -> Dict:
        """
        Timbre (음색) 특징 추출
        
        설명 가능한 음색 축:
        1. Brightness (밝기) - Spectral Centroid
        2. Roughness (거칠음) - Spectral Flatness
        3. Body (바디) - Low-Mid Band Energy Ratio
        4. Clarity (선명도) - HNR (Harmonics-to-Noise Ratio)
        5. Warmth (따뜻함) - Mid-Low Band Energy Ratio
        
        Args:
            audio: 전체 오디오
            segments: 세그먼트 리스트
        
        Returns:
            timbre_features: Dict
        """
        # 전체 오디오 Timbre
        timbre_global = self._extract_timbre_single(audio)
        
        # 세그먼트별 Timbre
        segment_stats = []
        for seg in segments:
            seg_timbre = self._extract_timbre_single(seg['audio'])
            seg_timbre['start_time'] = seg['start_time']
            seg_timbre['end_time'] = seg['end_time']
            segment_stats.append(seg_timbre)
        
        # 세그먼트 평균 (품질 가중)
        qualities = [seg['quality_score'] for seg in segments]
        weighted_timbre = self._weighted_average_timbre(segment_stats, qualities)
        
        # 성별 추정 (F0와 Formant 기반)
        gender = self._estimate_gender(weighted_timbre)
        
        print(f"✓ Timbre 추출 완료")
        print(f"  - 추정 성별: {gender}")
        print(f"  - F0 평균: {weighted_timbre['f0_mean']:.1f} Hz")
        print(f"  - Formant F1: {weighted_timbre['formant_f1']:.1f} Hz")
        print(f"  - Formant F2: {weighted_timbre['formant_f2']:.1f} Hz")
        print(f"  - 밝기 (Brightness): {weighted_timbre['brightness']:.3f}")
        print(f"  - 거칠음 (Roughness): {weighted_timbre['roughness']:.3f}")
        print(f"  - 바디 (Body): {weighted_timbre['body']:.3f}")
        print(f"  - 선명도 (Clarity): {weighted_timbre['clarity']:.3f}")
        print(f"  - 따뜻함 (Warmth): {weighted_timbre['warmth']:.3f}")
        
        return {
            'global': timbre_global,
            'weighted': weighted_timbre,
            'segment_stats': segment_stats,
            'gender': gender
        }
    
    def _extract_timbre_single(self, audio: np.ndarray) -> Dict:
        """단일 오디오 세그먼트에서 Timbre 추출 (개선 버전)"""
        # STFT
        n_fft = 2048
        hop_length = 512
        S = np.abs(librosa.stft(audio, n_fft=n_fft, hop_length=hop_length))
        freqs = librosa.fft_frequencies(sr=self.sr, n_fft=n_fft)
        
        # F0 추출 (상대적 분석에 사용)
        f0, voiced_flag, _ = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=self.sr
        )
        f0_mean = np.nanmedian(f0[voiced_flag]) if np.any(voiced_flag) else 200.0
        
        # 1. Brightness - Spectral Centroid (개선: 상대적 위치)
        centroid = librosa.feature.spectral_centroid(S=S, sr=self.sr, hop_length=hop_length)[0]
        centroid_mean = np.mean(centroid)
        
        # F0 대비 상대적 위치 (배음 구조 반영)
        # 남자(F0~120Hz): centroid 2000Hz면 상대적으로 밝음
        # 여자(F0~220Hz): centroid 2000Hz면 상대적으로 덜 밝음
        relative_brightness = centroid_mean / (f0_mean * 10)  # F0의 10배음 기준
        brightness = float(np.clip(relative_brightness / 2.0, 0, 1))  # 0~1 정규화
        
        # 2. Roughness - Spectral Flatness (유지)
        flatness = librosa.feature.spectral_flatness(S=S, hop_length=hop_length)[0]
        roughness = float(np.mean(flatness))
        
        # 3. Body - 상대적 저중역 에너지 (개선)
        # F0 기준으로 1~4배음 대역 (기본음 + 저역 배음)
        low_freq_min = max(50, f0_mean * 0.8)
        low_freq_max = min(self.sr / 2, f0_mean * 4)
        low_mask = (freqs >= low_freq_min) & (freqs <= low_freq_max)
        low_energy = np.sum(S[low_mask, :])
        
        # 중역 에너지 (4~8배음)
        mid_freq_min = low_freq_max
        mid_freq_max = min(self.sr / 2, f0_mean * 8)
        mid_mask = (freqs >= mid_freq_min) & (freqs <= mid_freq_max)
        mid_energy = np.sum(S[mid_mask, :])
        
        total_energy = np.sum(S)
        body = float(low_energy / total_energy) if total_energy > 0 else 0.0
        
        # 4. Clarity - HNR 추정 (유지)
        try:
            import parselmouth
            sound = parselmouth.Sound(audio, sampling_frequency=self.sr)
            harmonicity = sound.to_harmonicity()
            hnr_values = harmonicity.values[harmonicity.values > -200]
            clarity = float(np.mean(hnr_values) / 30.0) if len(hnr_values) > 0 else 0.0
            clarity = np.clip(clarity, 0, 1)
        except:
            # Parselmouth 없으면 Spectral Rolloff로 대체
            rolloff = librosa.feature.spectral_rolloff(S=S, sr=self.sr, hop_length=hop_length)[0]
            clarity = float(np.mean(rolloff) / (self.sr / 2))
        
        # 5. Warmth - 중저역 에너지 비율 (개선)
        # 2~6배음 대역 (따뜻함을 주는 중저역)
        warm_freq_min = max(100, f0_mean * 2)
        warm_freq_max = min(self.sr / 2, f0_mean * 6)
        warm_mask = (freqs >= warm_freq_min) & (freqs <= warm_freq_max)
        warm_energy = np.sum(S[warm_mask, :])
        warmth = float(warm_energy / total_energy) if total_energy > 0 else 0.0
        
        # 6. Formant 분석 추가 (성별/음색 구분에 중요)
        formants = self._extract_formants(audio)
        
        return {
            'brightness': brightness,
            'roughness': roughness,
            'body': body,
            'clarity': clarity,
            'warmth': warmth,
            'f0_mean': float(f0_mean),
            'formant_f1': formants['f1'],
            'formant_f2': formants['f2'],
            'spectral_centroid': float(centroid_mean)
        }
    
    def _extract_formants(self, audio: np.ndarray) -> Dict:
        """
        Formant 추출 (F1, F2)
        F1: 혀의 높이 (남자 ~500Hz, 여자 ~600Hz)
        F2: 혀의 앞뒤 위치 (남자 ~1500Hz, 여자 ~1800Hz)
        """
        try:
            import parselmouth
            sound = parselmouth.Sound(audio, sampling_frequency=self.sr)
            formants = sound.to_formant_burg()
            
            f1_values = []
            f2_values = []
            
            # 시간에 따른 formant 추출
            for t in np.linspace(0, sound.duration, min(50, int(sound.duration * 10))):
                f1 = formants.get_value_at_time(1, t)
                f2 = formants.get_value_at_time(2, t)
                
                if not np.isnan(f1) and f1 > 0:
                    f1_values.append(f1)
                if not np.isnan(f2) and f2 > 0:
                    f2_values.append(f2)
            
            f1_mean = float(np.median(f1_values)) if f1_values else 500.0
            f2_mean = float(np.median(f2_values)) if f2_values else 1500.0
            
        except:
            # Parselmouth 없으면 스펙트럼 피크로 추정
            S = np.abs(librosa.stft(audio, n_fft=2048))
            freqs = librosa.fft_frequencies(sr=self.sr, n_fft=2048)
            
            # 평균 스펙트럼
            spectrum = np.mean(S, axis=1)
            
            # F1 추정 (300-900Hz 범위에서 피크)
            f1_mask = (freqs >= 300) & (freqs <= 900)
            f1_spectrum = spectrum[f1_mask]
            f1_freqs = freqs[f1_mask]
            f1_peak_idx = np.argmax(f1_spectrum)
            f1_mean = float(f1_freqs[f1_peak_idx]) if len(f1_freqs) > 0 else 500.0
            
            # F2 추정 (900-2500Hz 범위에서 피크)
            f2_mask = (freqs >= 900) & (freqs <= 2500)
            f2_spectrum = spectrum[f2_mask]
            f2_freqs = freqs[f2_mask]
            f2_peak_idx = np.argmax(f2_spectrum)
            f2_mean = float(f2_freqs[f2_peak_idx]) if len(f2_freqs) > 0 else 1500.0
        
        return {
            'f1': f1_mean,
            'f2': f2_mean
        }
    
    def _weighted_average_timbre(
        self,
        segment_timbres: List[Dict],
        qualities: List[float]
    ) -> Dict:
        """품질 가중 평균 Timbre 계산 (개선 버전)"""
        qualities = np.array(qualities)
        qualities = qualities / np.sum(qualities)  # 정규화
        
        weighted = {
            'brightness': 0.0,
            'roughness': 0.0,
            'body': 0.0,
            'clarity': 0.0,
            'warmth': 0.0,
            'f0_mean': 0.0,
            'formant_f1': 0.0,
            'formant_f2': 0.0,
            'spectral_centroid': 0.0
        }
        
        for timbre, weight in zip(segment_timbres, qualities):
            weighted['brightness'] += timbre['brightness'] * weight
            weighted['roughness'] += timbre['roughness'] * weight
            weighted['body'] += timbre['body'] * weight
            weighted['clarity'] += timbre['clarity'] * weight
            weighted['warmth'] += timbre['warmth'] * weight
            weighted['f0_mean'] += timbre['f0_mean'] * weight
            weighted['formant_f1'] += timbre['formant_f1'] * weight
            weighted['formant_f2'] += timbre['formant_f2'] * weight
            weighted['spectral_centroid'] += timbre['spectral_centroid'] * weight
        
        return weighted
    
    def _estimate_gender(self, timbre: Dict) -> str:
        """
        성별 추정 (F0와 Formant 기반)
        
        기준:
        - 남자: F0 < 165Hz, F1 < 550Hz
        - 여자: F0 > 165Hz, F1 > 550Hz
        
        Args:
            timbre: 음색 특징
        
        Returns:
            'male' or 'female'
        """
        f0 = timbre['f0_mean']
        f1 = timbre['formant_f1']
        
        # F0 기준 점수 (0~1, 1이면 여자)
        f0_score = (f0 - 100) / (250 - 100)  # 100~250Hz 범위
        f0_score = np.clip(f0_score, 0, 1)
        
        # F1 기준 점수 (0~1, 1이면 여자)
        f1_score = (f1 - 450) / (650 - 450)  # 450~650Hz 범위
        f1_score = np.clip(f1_score, 0, 1)
        
        # 종합 점수 (F0 가중치 60%, F1 가중치 40%)
        gender_score = f0_score * 0.6 + f1_score * 0.4
        
        if gender_score > 0.5:
            return 'female'
        else:
            return 'male'
    
    # ========================================
    # 5. ECAPA-TDNN 임베딩 추출
    # ========================================
    
    def extract_ecapa_embedding(self, segments: List[Dict], max_segments: Optional[int] = None) -> Dict:
        """
        ECAPA-TDNN 임베딩 추출
        
        화자 인식 모델을 사용하여 보컬의 전반적 컬러/발성 습관을 압축
        
        추출 방식:
        1. 세그먼트 선택 (품질 + 시간 분포 고려)
        2. 세그먼트별 임베딩 계산
        3. 품질 가중 평균으로 대표 임베딩 생성
        
        Args:
            segments: 세그먼트 리스트
            max_segments: 최대 사용할 세그먼트 개수 (None이면 모두 사용)
                         속도 최적화를 위해 5개 권장 (정확도와 속도의 균형)
        
        Returns:
            embedding_features: {
                'representative': 대표 임베딩 (192-dim),
                'segment_embeddings': 세그먼트별 임베딩 리스트
            }
        """
        # ECAPA 모델 로드 (lazy loading, 클래스 변수로 공유)
        if FeatureExtractor._ecapa_classifier is None:
            FeatureExtractor._load_ecapa_model()
        
        import torch
        
        # 세그먼트 선택 전략: 품질 + 시간 분포 고려
        if max_segments is not None and len(segments) > max_segments:
            selected_segments = self._select_representative_segments(segments, max_segments)
            print(f"  ⚡ 속도 최적화: {len(segments)}개 중 {len(selected_segments)}개 세그먼트 선택")
            print(f"     (품질 상위 + 시간 분포 고려)")
        else:
            selected_segments = segments
        
        segment_embeddings = []
        qualities = []
        
        for seg in selected_segments:
            # 오디오 → 텐서
            audio_tensor = torch.FloatTensor(seg['audio']).unsqueeze(0)
            
            # 임베딩 추출
            with torch.no_grad():
                embedding = FeatureExtractor._ecapa_classifier.encode_batch(audio_tensor)
                embedding = embedding.squeeze().cpu().numpy()
            
            segment_embeddings.append(embedding)
            qualities.append(seg['quality_score'])
        
        # 품질 가중 평균
        qualities = np.array(qualities)
        qualities = qualities / np.sum(qualities)  # 정규화
        
        representative = np.average(segment_embeddings, axis=0, weights=qualities)
        
        print(f"✓ ECAPA 임베딩 추출 완료")
        print(f"  - 임베딩 차원: {representative.shape[0]}")
        print(f"  - 사용된 세그먼트: {len(segment_embeddings)}개")
        
        return {
            'representative': representative.tolist(),
            'segment_embeddings': [emb.tolist() for emb in segment_embeddings],
            'embedding_dim': int(representative.shape[0])
        }
    
    def _select_representative_segments(self, segments: List[Dict], max_segments: int) -> List[Dict]:
        """
        대표 세그먼트 선택 (품질 + 시간 분포 고려)
        
        전략:
        1. 품질 상위 50% 세그먼트 중에서 선택
        2. 시간적으로 균등하게 분산된 세그먼트 선택
        3. 최종적으로 max_segments개 선택
        
        Args:
            segments: 전체 세그먼트 리스트
            max_segments: 선택할 최대 세그먼트 개수
        
        Returns:
            selected_segments: 선택된 세그먼트 리스트
        """
        if len(segments) <= max_segments:
            return segments
        
        # 1. 품질 점수 기준 정렬
        sorted_segments = sorted(segments, key=lambda x: x['quality_score'], reverse=True)
        
        # 2. 상위 50% 또는 최소 max_segments * 2개 중에서 선택
        top_candidates = sorted_segments[:max(len(sorted_segments) // 2, max_segments * 2)]
        
        # 3. 시간 분포 고려하여 선택
        # 각 세그먼트의 중간 시간 계산
        for seg in top_candidates:
            seg['mid_time'] = (seg['start_time'] + seg['end_time']) / 2
        
        # 시간 구간을 max_segments개로 나눔
        if len(top_candidates) <= max_segments:
            return top_candidates
        
        # 시간 구간별로 최고 품질 세그먼트 선택
        total_duration = max(seg['end_time'] for seg in top_candidates)
        time_bins = np.linspace(0, total_duration, max_segments + 1)
        
        selected = []
        for i in range(len(time_bins) - 1):
            bin_start = time_bins[i]
            bin_end = time_bins[i + 1]
            
            # 해당 시간 구간의 세그먼트 찾기
            bin_segments = [
                seg for seg in top_candidates
                if bin_start <= seg['mid_time'] < bin_end
            ]
            
            if bin_segments:
                # 품질이 가장 높은 것 선택
                best = max(bin_segments, key=lambda x: x['quality_score'])
                selected.append(best)
            else:
                # 구간에 세그먼트가 없으면 가장 가까운 것 선택
                closest = min(
                    top_candidates,
                    key=lambda x: abs(x['mid_time'] - (bin_start + bin_end) / 2)
                )
                if closest not in selected:
                    selected.append(closest)
        
        # 중복 제거 및 품질 순 정렬
        selected = list({id(seg): seg for seg in selected}.values())
        selected = sorted(selected, key=lambda x: x['quality_score'], reverse=True)
        
        # 정확히 max_segments개만 반환
        return selected[:max_segments]
    
    @classmethod
    def _load_ecapa_model(cls):
        """
        ECAPA-TDNN 모델 로드 (클래스 메서드로 공유)
        
        프로덕션 환경에서도 동일하게 작동:
        - 첫 번째 인스턴스 생성 시 모델 로드
        - 이후 모든 인스턴스가 동일한 모델 인스턴스 재사용
        - 메모리 효율성 및 성능 최적화
        """
        if cls._ecapa_classifier is not None:
            print("✓ ECAPA-TDNN 모델 재사용 (이미 로드됨)")
            return
        
        try:
            from speechbrain.pretrained import EncoderClassifier
            
            print("⏳ ECAPA-TDNN 모델 로딩 중...")
            cls._ecapa_classifier = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained_models/spkrec-ecapa-voxceleb"
            )
            cls._ecapa_model_loaded = True
            print("✓ ECAPA-TDNN 모델 로드 완료")
        except ImportError:
            print("⚠️  SpeechBrain이 설치되지 않았습니다.")
            print("   pip install speechbrain 로 설치해주세요.")
            raise
        except Exception as e:
            print(f"❌ ECAPA 모델 로드 실패: {e}")
            raise


# 테스트용
if __name__ == "__main__":
    from audio_preprocessing import AudioPreprocessor
    from pathlib import Path
    
    # 테스트 오디오
    test_audio = "test_vocal.wav"
    
    if Path(test_audio).exists():
        # 1. 전처리
        preprocessor = AudioPreprocessor()
        audio, segments = preprocessor.preprocess(test_audio)
        
        # 2. 특징 추출
        extractor = FeatureExtractor(sr=16000)
        features = extractor.extract_all_features(audio, segments)
        
        print("\n=== 추출된 특징 요약 ===")
        print(f"Pitch: {features['pitch']['f0_min']:.1f}Hz ~ {features['pitch']['f0_max']:.1f}Hz")
        print(f"Energy: {features['energy']['rms_mean']:.4f}")
        print(f"Onset: {len(features['onset']['onset_times'])}개")
        print(f"Timbre: {features['timbre']['weighted']}")
        print(f"Embedding: {features['embedding']['embedding_dim']}차원")
    else:
        print(f"테스트 파일이 없습니다: {test_audio}")


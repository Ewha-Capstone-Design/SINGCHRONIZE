"""
고급 보컬 분석 모듈
- 음정 정확도 분석 (음계 추적)
- 비브라토 분석
- 발성 기술 분석 (Belting, Head Voice, Mix Voice)
- 고급 음색 분석 (MFCC, Formant)
"""
import numpy as np
import librosa
from typing import Dict, List, Tuple, Optional
from scipy import signal
from scipy.stats import linregress


class AdvancedVocalAnalyzer:
    """고급 보컬 분석 클래스"""
    
    def __init__(self, sr: int = 16000):
        self.sr = sr
    
    # ========================================
    # 1. 음정 정확도 분석
    # ========================================
    
    def analyze_pitch_accuracy(
        self,
        f0_contour: np.ndarray,
        voiced_mask: np.ndarray,
        time: np.ndarray
    ) -> Dict:
        """
        음정 정확도 분석
        
        평가 기준:
        1. 음정 안정성 (각 음표 내에서 F0 떨림)
        2. 음정 전환 정확도 (음정 변화 시 정확도)
        3. 음정 유지 능력 (긴 음표 유지)
        
        Args:
            f0_contour: F0 변화 곡선
            voiced_mask: 유성음 마스크
            time: 시간 배열
        
        Returns:
            accuracy_features: Dict
        """
        # numpy array로 변환
        f0_contour = np.array(f0_contour)
        voiced_mask = np.array(voiced_mask, dtype=bool)
        time = np.array(time)
        
        f0_voiced = f0_contour[voiced_mask]
        time_voiced = time[voiced_mask]
        
        if len(f0_voiced) < 10:
            return self._empty_pitch_accuracy()
        
        # 1. 음표 세그먼테이션 (연속된 비슷한 F0를 하나의 음표로)
        notes = self._segment_into_notes(f0_voiced, time_voiced)
        
        # 2. 각 음표의 안정성 분석
        note_stabilities = []
        note_accuracies = []
        
        for note in notes:
            if len(note['f0']) < 5:
                continue
            
            # 목표 음정 (중앙값)
            target_f0 = np.median(note['f0'])
            
            # 음정 안정성 (cent 단위 편차)
            cents_deviation = 1200 * np.log2(note['f0'] / target_f0)
            stability = np.std(cents_deviation)  # cent 단위
            note_stabilities.append(stability)
            
            # 음정 정확도 (가장 가까운 반음과의 거리)
            target_midi = librosa.hz_to_midi(target_f0)
            nearest_midi = np.round(target_midi)
            cents_off = (target_midi - nearest_midi) * 100
            note_accuracies.append(abs(cents_off))
        
        # 3. 음정 전환 분석
        pitch_transitions = self._analyze_pitch_transitions(notes)
        
        # 4. 종합 점수 계산
        avg_stability = np.mean(note_stabilities) if note_stabilities else 50.0
        avg_accuracy = np.mean(note_accuracies) if note_accuracies else 50.0
        
        # 점수화 (0~100) - 기준 완화
        # 안정성: 20 cent 이하 = 100점, 80 cent 이상 = 0점 (실제 노래는 떨림 있음)
        stability_score = np.clip(100 - (avg_stability - 20) * 1.67, 0, 100)
        
        # 정확도: 25 cent 이하 = 100점, 75 cent 이상 = 0점 (1/4 반음 이내면 OK)
        accuracy_score = np.clip(100 - (avg_accuracy - 25) * 2.0, 0, 100)
        
        return {
            'stability_score': float(stability_score),
            'accuracy_score': float(accuracy_score),
            'avg_stability_cents': float(avg_stability),
            'avg_accuracy_cents': float(avg_accuracy),
            'num_notes': len(notes),
            'transition_smoothness': pitch_transitions['smoothness'],
            'notes': notes[:10]  # 처음 10개만 저장
        }
    
    def _segment_into_notes(
        self,
        f0: np.ndarray,
        time: np.ndarray
    ) -> List[Dict]:
        """F0 contour를 개별 음표로 분할"""
        notes = []
        
        # 반음 단위로 변환
        midi = librosa.hz_to_midi(f0)
        
        # 음정 변화 감지 (0.5 반음 이상 변화)
        diff = np.abs(np.diff(midi))
        change_points = np.where(diff > 0.5)[0] + 1
        
        # 세그먼트 생성
        segments = np.split(np.arange(len(f0)), change_points)
        
        for seg_idx in segments:
            if len(seg_idx) < 5:  # 너무 짧은 음표 제외
                continue
            
            note_f0 = f0[seg_idx]
            note_time = time[seg_idx]
            
            notes.append({
                'f0': note_f0,
                'time': note_time,
                'duration': note_time[-1] - note_time[0],
                'median_f0': np.median(note_f0),
                'median_midi': librosa.hz_to_midi(np.median(note_f0))
            })
        
        return notes
    
    def _analyze_pitch_transitions(self, notes: List[Dict]) -> Dict:
        """음정 전환 분석"""
        if len(notes) < 2:
            return {'smoothness': 100.0, 'num_transitions': 0}
        
        smoothness_scores = []
        
        for i in range(len(notes) - 1):
            # 전환 구간의 F0 변화 분석
            # 부드러운 전환 vs 급격한 점프
            f0_start = notes[i]['median_f0']
            f0_end = notes[i + 1]['median_f0']
            
            # 반음 차이
            semitone_diff = abs(librosa.hz_to_midi(f0_end) - librosa.hz_to_midi(f0_start))
            
            # 큰 도약은 자연스러움 (옥타브 점프 등)
            # 작은 도약은 정확해야 함
            if semitone_diff > 7:  # 5도 이상
                smoothness = 100.0  # 큰 도약은 OK
            else:
                # 작은 도약의 정확도
                smoothness = 100.0  # 일단 100으로 (실제로는 전환 구간 분석 필요)
            
            smoothness_scores.append(smoothness)
        
        return {
            'smoothness': float(np.mean(smoothness_scores)),
            'num_transitions': len(smoothness_scores)
        }
    
    def _empty_pitch_accuracy(self) -> Dict:
        return {
            'stability_score': 0.0,
            'accuracy_score': 0.0,
            'avg_stability_cents': 0.0,
            'avg_accuracy_cents': 0.0,
            'num_notes': 0,
            'transition_smoothness': 0.0,
            'notes': []
        }
    
    # ========================================
    # 2. 비브라토 분석
    # ========================================
    
    def analyze_vibrato(
        self,
        f0_contour: np.ndarray,
        voiced_mask: np.ndarray,
        time: np.ndarray
    ) -> Dict:
        """
        비브라토 분석
        
        비브라토 특성:
        1. Rate (속도): 5-8 Hz가 자연스러움
        2. Extent (폭): 반음의 ±5-10%
        3. Regularity (규칙성): 주기적일수록 좋음
        
        Args:
            f0_contour: F0 변화 곡선
            voiced_mask: 유성음 마스크
            time: 시간 배열
        
        Returns:
            vibrato_features: Dict
        """
        # numpy array로 변환
        f0_contour = np.array(f0_contour)
        voiced_mask = np.array(voiced_mask, dtype=bool)
        time = np.array(time)
        
        f0_voiced = f0_contour[voiced_mask]
        time_voiced = time[voiced_mask]
        
        if len(f0_voiced) < 50:
            return self._empty_vibrato()
        
        # 1. 장기 트렌드 제거 (비브라토만 남김)
        # Savitzky-Golay 필터로 평활화
        window_length = min(51, len(f0_voiced) if len(f0_voiced) % 2 == 1 else len(f0_voiced) - 1)
        if window_length < 5:
            return self._empty_vibrato()
        
        f0_smooth = signal.savgol_filter(f0_voiced, window_length, 3)
        vibrato_signal = f0_voiced - f0_smooth
        
        # 2. 비브라토 감지
        # FFT로 주파수 분석
        fft = np.fft.fft(vibrato_signal)
        freqs = np.fft.fftfreq(len(vibrato_signal), d=np.mean(np.diff(time_voiced)))
        
        # 양의 주파수만
        pos_mask = freqs > 0
        freqs = freqs[pos_mask]
        fft_mag = np.abs(fft[pos_mask])
        
        # 비브라토 범위 (4-9 Hz)
        vibrato_mask = (freqs >= 4) & (freqs <= 9)
        
        if np.sum(vibrato_mask) == 0:
            return self._empty_vibrato()
        
        vibrato_freqs = freqs[vibrato_mask]
        vibrato_mags = fft_mag[vibrato_mask]
        
        # 가장 강한 비브라토 주파수
        peak_idx = np.argmax(vibrato_mags)
        vibrato_rate = vibrato_freqs[peak_idx]
        vibrato_strength = vibrato_mags[peak_idx] / np.sum(fft_mag)
        
        # 3. 비브라토 폭 (Extent)
        vibrato_extent_hz = np.std(vibrato_signal) * 2  # ±1 std
        vibrato_extent_cents = 1200 * np.log2((f0_smooth.mean() + vibrato_extent_hz) / f0_smooth.mean())
        
        # 4. 비브라토 규칙성 (주기성)
        # 자기상관함수로 측정
        autocorr = np.correlate(vibrato_signal, vibrato_signal, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        
        # 첫 번째 피크 찾기 (주기)
        peaks, _ = signal.find_peaks(autocorr, distance=10)
        regularity = autocorr[peaks[0]] / autocorr[0] if len(peaks) > 0 else 0.0
        
        # 5. 점수화
        # Rate 점수: 5-7 Hz가 이상적
        rate_score = 100 - abs(vibrato_rate - 6) * 20
        rate_score = np.clip(rate_score, 0, 100)
        
        # Extent 점수: 50-100 cents가 이상적
        extent_score = 100 - abs(vibrato_extent_cents - 75) * 2
        extent_score = np.clip(extent_score, 0, 100)
        
        # Regularity 점수
        regularity_score = regularity * 100
        
        # 비브라토 사용 여부 (strength > 0.1이면 사용)
        has_vibrato = vibrato_strength > 0.1
        
        return {
            'has_vibrato': bool(has_vibrato),
            'rate_hz': float(vibrato_rate),
            'extent_cents': float(vibrato_extent_cents),
            'regularity': float(regularity),
            'strength': float(vibrato_strength),
            'rate_score': float(rate_score),
            'extent_score': float(extent_score),
            'regularity_score': float(regularity_score),
            'overall_score': float((rate_score + extent_score + regularity_score) / 3) if has_vibrato else 0.0
        }
    
    def _empty_vibrato(self) -> Dict:
        return {
            'has_vibrato': False,
            'rate_hz': 0.0,
            'extent_cents': 0.0,
            'regularity': 0.0,
            'strength': 0.0,
            'rate_score': 0.0,
            'extent_score': 0.0,
            'regularity_score': 0.0,
            'overall_score': 0.0
        }
    
    # ========================================
    # 3. 발성 기술 분석
    # ========================================
    
    def analyze_vocal_technique(
        self,
        audio: np.ndarray,
        f0_contour: np.ndarray,
        voiced_mask: np.ndarray,
        energy: np.ndarray
    ) -> Dict:
        """
        발성 기술 분석
        
        분석 항목:
        1. Belting (벨팅) - 고음역 + 높은 에너지 + 강한 배음
        2. Head Voice (두성) - 고음역 + 낮은 에너지 + 약한 배음
        3. Mix Voice (믹스) - 중음역 + 균형잡힌 에너지
        4. Breathy (기식) - 높은 Spectral Flatness
        5. Resonance (공명) - Formant 집중도
        
        Args:
            audio: 오디오 신호
            f0_contour: F0 변화 곡선
            voiced_mask: 유성음 마스크
            energy: RMS 에너지
        
        Returns:
            technique_features: Dict
        """
        # STFT
        S = np.abs(librosa.stft(audio, n_fft=2048, hop_length=512))
        freqs = librosa.fft_frequencies(sr=self.sr, n_fft=2048)
        
        # numpy array로 변환
        f0_contour = np.array(f0_contour)
        voiced_mask = np.array(voiced_mask, dtype=bool)
        
        # F0 정보
        f0_voiced = f0_contour[voiced_mask]
        if len(f0_voiced) == 0:
            return self._empty_technique()
        
        f0_median = np.median(f0_voiced)
        
        # 1. 음역대 분류
        if f0_median > 400:  # 고음역 (G4 이상)
            register = 'high'
        elif f0_median > 250:  # 중음역 (B3~G4)
            register = 'mid'
        else:  # 저음역
            register = 'low'
        
        # 2. 배음 강도 분석
        # F0의 2~5배음 에너지
        harmonic_energy = self._analyze_harmonics(S, freqs, f0_median)
        
        # 3. Spectral Flatness (기식성)
        flatness = librosa.feature.spectral_flatness(S=S)[0]
        breathiness = np.mean(flatness)
        
        # 4. 발성 기술 분류
        techniques = []
        technique_scores = {}
        
        # Belting 감지: 고음역 + 높은 에너지 + 강한 배음
        if register == 'high' and harmonic_energy > 0.3:
            belting_score = harmonic_energy * 100
            techniques.append('belting')
            technique_scores['belting'] = float(belting_score)
        else:
            technique_scores['belting'] = 0.0
        
        # Head Voice 감지: 고음역 + 약한 배음
        if register == 'high' and harmonic_energy < 0.2:
            head_voice_score = (1 - harmonic_energy) * 100
            techniques.append('head_voice')
            technique_scores['head_voice'] = float(head_voice_score)
        else:
            technique_scores['head_voice'] = 0.0
        
        # Mix Voice 감지: 중음역 + 균형
        if register == 'mid' and 0.2 <= harmonic_energy <= 0.4:
            mix_voice_score = 100 - abs(harmonic_energy - 0.3) * 300
            techniques.append('mix_voice')
            technique_scores['mix_voice'] = float(mix_voice_score)
        else:
            technique_scores['mix_voice'] = 0.0
        
        # Breathy 감지: 높은 flatness
        if breathiness > 0.1:
            breathy_score = breathiness * 500
            breathy_score = min(breathy_score, 100)
            techniques.append('breathy')
            technique_scores['breathy'] = float(breathy_score)
        else:
            technique_scores['breathy'] = 0.0
        
        # 5. 공명 분석
        resonance_score = self._analyze_resonance(S, freqs)
        
        return {
            'register': register,
            'techniques': techniques,
            'technique_scores': technique_scores,
            'harmonic_energy': float(harmonic_energy),
            'breathiness': float(breathiness),
            'resonance_score': float(resonance_score),
            'overall_technique_score': float(np.mean(list(technique_scores.values())))
        }
    
    def _analyze_harmonics(
        self,
        S: np.ndarray,
        freqs: np.ndarray,
        f0: float
    ) -> float:
        """배음 에너지 분석"""
        if f0 < 50:
            return 0.0
        
        # 2~5배음 에너지 합
        harmonic_energy = 0.0
        total_energy = np.sum(S)
        
        if total_energy == 0:
            return 0.0
        
        for h in range(2, 6):
            harmonic_f = f0 * h
            if harmonic_f > self.sr / 2:
                break
            
            # 해당 주파수 주변 에너지
            mask = (freqs >= harmonic_f * 0.9) & (freqs <= harmonic_f * 1.1)
            harmonic_energy += np.sum(S[mask, :])
        
        return harmonic_energy / total_energy
    
    def _analyze_resonance(self, S: np.ndarray, freqs: np.ndarray) -> float:
        """공명 분석 (Formant 집중도)"""
        # 평균 스펙트럼
        spectrum = np.mean(S, axis=1)
        
        # 300-3000Hz 범위에서 피크 찾기
        mask = (freqs >= 300) & (freqs <= 3000)
        spectrum_band = spectrum[mask]
        
        if len(spectrum_band) == 0:
            return 0.0
        
        # 피크 찾기
        peaks, properties = signal.find_peaks(spectrum_band, prominence=np.max(spectrum_band) * 0.1)
        
        # 피크가 많고 뚜렷할수록 공명이 좋음
        if len(peaks) == 0:
            return 0.0
        
        # 피크 prominence 평균
        avg_prominence = np.mean(properties['prominences'])
        max_spectrum = np.max(spectrum_band)
        
        resonance = (avg_prominence / max_spectrum) * 100 if max_spectrum > 0 else 0.0
        return min(resonance, 100.0)
    
    def _empty_technique(self) -> Dict:
        return {
            'register': 'unknown',
            'techniques': [],
            'technique_scores': {
                'belting': 0.0,
                'head_voice': 0.0,
                'mix_voice': 0.0,
                'breathy': 0.0
            },
            'harmonic_energy': 0.0,
            'breathiness': 0.0,
            'resonance_score': 0.0,
            'overall_technique_score': 0.0
        }
    
    # ========================================
    # 4. 가성/진성 분석 (Voice Register Analysis)
    # ========================================
    
    def analyze_voice_register(
        self,
        audio: np.ndarray,
        f0_contour: np.ndarray,
        voiced_mask: np.ndarray
    ) -> Dict:
        """
        가성/진성/믹스 보이스 분석
        
        분석 방법:
        1. F0와 배음 구조로 레지스터 판별
        2. 가성: 고음역 + 약한 배음 + 낮은 에너지
        3. 진성: 중저음역 + 강한 배음 + 높은 에너지
        4. 믹스: 중음역 + 균형잡힌 배음
        
        Args:
            audio: 오디오 신호
            f0_contour: F0 변화 곡선
            voiced_mask: 유성음 마스크
        
        Returns:
            register_features: Dict
        """
        # numpy array로 변환
        f0_contour = np.array(f0_contour)
        voiced_mask = np.array(voiced_mask, dtype=bool)
        
        f0_voiced = f0_contour[voiced_mask]
        
        if len(f0_voiced) < 10:
            return self._empty_register()
        
        # STFT
        S = np.abs(librosa.stft(audio, n_fft=2048, hop_length=512))
        freqs = librosa.fft_frequencies(sr=self.sr, n_fft=2048)
        
        # 프레임별 분석
        hop_length = 512
        frame_length = len(audio) // hop_length + 1
        
        # F0를 프레임 길이에 맞게 리샘플링
        if len(f0_contour) > frame_length:
            f0_resampled = f0_contour[:frame_length]
            voiced_resampled = voiced_mask[:frame_length]
        else:
            # 패딩
            f0_resampled = np.pad(f0_contour, (0, frame_length - len(f0_contour)), constant_values=0)
            voiced_resampled = np.pad(voiced_mask, (0, frame_length - len(voiced_mask)), constant_values=False)
        
        # 각 프레임의 레지스터 판별
        registers = []
        
        for i in range(min(len(f0_resampled), S.shape[1])):
            if not voiced_resampled[i] or f0_resampled[i] < 50:
                continue
            
            f0 = f0_resampled[i]
            spectrum = S[:, i]
            
            # 1. F0 기준 음역대
            if f0 > 350:  # 고음역 (F4 이상)
                pitch_register = 'high'
            elif f0 > 200:  # 중음역 (G3~F4)
                pitch_register = 'mid'
            else:  # 저음역
                pitch_register = 'low'
            
            # 2. 배음 강도 분석
            harmonic_strength = self._calculate_harmonic_strength(spectrum, freqs, f0)
            
            # 3. 에너지 분석
            frame_energy = np.sum(spectrum)
            
            # 4. 레지스터 판별
            if pitch_register == 'high' and harmonic_strength < 0.15:
                # 고음역 + 약한 배음 = 가성
                registers.append('falsetto')
            elif pitch_register == 'low' and harmonic_strength > 0.25:
                # 저음역 + 강한 배음 = 진성
                registers.append('chest')
            elif pitch_register == 'mid':
                # 중음역 = 믹스 (또는 진성/가성 중간)
                if harmonic_strength > 0.25:
                    registers.append('chest')  # 진성 쪽
                elif harmonic_strength < 0.15:
                    registers.append('falsetto')  # 가성 쪽
                else:
                    registers.append('mix')  # 믹스
            else:
                # 기타
                if harmonic_strength > 0.2:
                    registers.append('chest')
                else:
                    registers.append('mix')
        
        if not registers:
            return self._empty_register()
        
        # 비율 계산
        total = len(registers)
        chest_ratio = registers.count('chest') / total
        falsetto_ratio = registers.count('falsetto') / total
        mix_ratio = registers.count('mix') / total
        
        # 주 레지스터 판별
        if chest_ratio > 0.5:
            dominant_register = 'chest'
        elif falsetto_ratio > 0.3:
            dominant_register = 'falsetto'
        elif mix_ratio > 0.4:
            dominant_register = 'mix'
        else:
            dominant_register = 'chest'  # 기본값
        
        # 점수화 (0~100)
        # 다양한 레지스터 사용 = 높은 점수
        register_variety = 1 - max(chest_ratio, falsetto_ratio, mix_ratio)
        variety_score = register_variety * 200  # 0~1 → 0~200, clip to 100
        variety_score = np.clip(variety_score, 0, 100)
        
        return {
            'chest_ratio': float(chest_ratio),
            'falsetto_ratio': float(falsetto_ratio),
            'mix_ratio': float(mix_ratio),
            'dominant_register': dominant_register,
            'variety_score': float(variety_score),
            'description': self._describe_register(chest_ratio, falsetto_ratio, mix_ratio, dominant_register)
        }
    
    def _calculate_harmonic_strength(self, spectrum: np.ndarray, freqs: np.ndarray, f0: float) -> float:
        """배음 강도 계산"""
        if f0 < 50:
            return 0.0
        
        harmonic_energy = 0.0
        total_energy = np.sum(spectrum)
        
        if total_energy == 0:
            return 0.0
        
        # 2~5배음 에너지
        for h in range(2, 6):
            harmonic_f = f0 * h
            if harmonic_f > self.sr / 2:
                break
            
            # 해당 주파수 주변 에너지
            mask = (freqs >= harmonic_f * 0.9) & (freqs <= harmonic_f * 1.1)
            harmonic_energy += np.sum(spectrum[mask])
        
        return harmonic_energy / total_energy
    
    def _describe_register(self, chest: float, falsetto: float, mix: float, dominant: str) -> str:
        """레지스터 설명"""
        descriptions = []
        
        if chest > 0.6:
            descriptions.append("주로 진성(Chest Voice) 사용")
        elif chest > 0.3:
            descriptions.append("진성 적절히 사용")
        
        if falsetto > 0.3:
            descriptions.append("가성(Falsetto) 활용")
        elif falsetto > 0.1:
            descriptions.append("가성 부분적 사용")
        
        if mix > 0.4:
            descriptions.append("믹스 보이스 능숙")
        
        if not descriptions:
            descriptions.append(f"{dominant} 위주 발성")
        
        return ", ".join(descriptions)
    
    def _empty_register(self) -> Dict:
        return {
            'chest_ratio': 0.0,
            'falsetto_ratio': 0.0,
            'mix_ratio': 0.0,
            'dominant_register': 'unknown',
            'variety_score': 0.0,
            'description': '분석 불가'
        }
    
    # ========================================
    # 5. 고급 음색 분석 (MFCC)
    # ========================================
    
    def analyze_advanced_timbre(
        self,
        audio: np.ndarray
    ) -> Dict:
        """
        고급 음색 분석 (MFCC 기반)
        
        MFCC (Mel-Frequency Cepstral Coefficients):
        - 음성 인식의 표준 특징
        - 13개 계수로 음색 표현
        
        Args:
            audio: 오디오 신호
        
        Returns:
            advanced_timbre: Dict
        """
        # MFCC 추출
        mfcc = librosa.feature.mfcc(y=audio, sr=self.sr, n_mfcc=13)
        
        # 통계
        mfcc_mean = np.mean(mfcc, axis=1)
        mfcc_std = np.std(mfcc, axis=1)
        
        # MFCC 기반 음색 특성
        # MFCC 1: 전체 에너지/음량
        # MFCC 2-4: 음색의 밝기/어둡기
        # MFCC 5-13: 세부 음색 특성
        
        brightness_mfcc = float(np.mean(mfcc_mean[1:4]))  # MFCC 2-4
        richness_mfcc = float(np.mean(mfcc_mean[4:8]))    # MFCC 5-8
        texture_mfcc = float(np.std(mfcc_mean[8:13]))     # MFCC 9-13 변동
        
        # 정규화 (대략적)
        brightness_mfcc = (brightness_mfcc + 50) / 100
        brightness_mfcc = np.clip(brightness_mfcc, 0, 1)
        
        richness_mfcc = (richness_mfcc + 30) / 60
        richness_mfcc = np.clip(richness_mfcc, 0, 1)
        
        texture_mfcc = texture_mfcc / 20
        texture_mfcc = np.clip(texture_mfcc, 0, 1)
        
        return {
            'mfcc_mean': mfcc_mean.tolist(),
            'mfcc_std': mfcc_std.tolist(),
            'brightness_mfcc': float(brightness_mfcc),
            'richness_mfcc': float(richness_mfcc),
            'texture_mfcc': float(texture_mfcc)
        }


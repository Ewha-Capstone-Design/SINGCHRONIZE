"""
보컬 분석 리포트 생성 모듈 V2 (전문가 수준)
- 레이더 차트 (5개 품질 지표) - 재설계
- 음역대 분석
- 고급 음색 분석
- 발성 기술 평가
- 비브라토 분석
"""
import numpy as np
import librosa
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    from .radar_chart_descriptions import RADAR_CHART_DESCRIPTIONS, get_score_interpretation
except ImportError:
    from radar_chart_descriptions import RADAR_CHART_DESCRIPTIONS, get_score_interpretation


# 음색 5축 raw(value) → UI용 display_score (해석·구간 로직은 기존 value 그대로 유지)
TIMBRE_DISPLAY_SCORE_RANGES = {
    "brightness": {"low": 0.08, "high": 0.30},
    "roughness": {"low": 0.02, "high": 0.18},
    "body": {"low": 0.20, "high": 0.70},
    "clarity": {"low": 0.20, "high": 0.75},
    "warmth": {"low": 0.10, "high": 0.50},
}


def normalize_timbre_raw_to_0_100(value: float, low: float, high: float) -> float:
    if high <= low:
        return 50.0
    score = (value - low) / (high - low) * 100.0
    return float(max(0.0, min(100.0, score)))


def timbre_display_score_from_raw(axis_key: str, raw_value: float) -> int:
    """
    1) 축별 [low, high]로 0~100 정규화
    2) UI용 상향: display = 20 + 0.8 * normalized → 정수 반올림
    """
    spec = TIMBRE_DISPLAY_SCORE_RANGES.get(axis_key)
    if not spec:
        return int(round(max(0.0, min(100.0, raw_value * 100.0))))
    n = normalize_timbre_raw_to_0_100(raw_value, spec["low"], spec["high"])
    display = 20.0 + 0.8 * n
    return int(round(max(0.0, min(100.0, display))))


class ReportGeneratorV2:
    """
    보컬 분석 리포트 생성 클래스 V2
    
    레이더 차트 5축 (안정형 MVP):
    1. 음정 안정도 (Pitch Stability) - F0 변동 + 급변 구간 비율
    2. 리듬 안정도 (Rhythm Stability) - IOI 변동 + tempo drift
    3. 강약 조절 (Dynamic Control) - 다이나믹 범위 + 부드러움 (연속형)
    4. 발성 선명도 (Vocal Clarity) - HNR + Spectral Flatness
    5. 고음 유지력 (High Note Stability) - 고음 구간 안정성
    """
    
    def __init__(self):
        pass

    # 음색 프로필 interpretation용 5단계 (중간 구간을 넓게 쓰기 위한 공통 라벨)
    _TIER_5 = ("매우 낮음", "낮은 편", "중간", "높은 편", "매우 높음")
    
    def generate_report(self, features: Dict) -> Dict:
        """
        전체 리포트 생성 (아카펠라 전용)
        
        Args:
            features: extract_all_features()의 출력
        
        Returns:
            report: {
                'radar_chart': {...},
                'vocal_range': {...},
                'timbre_profile': {...},
                'genre_fitness': {...}
            }
        """
        print("\n" + "="*60)
        print("📊 보컬 분석 리포트 생성 (아카펠라 전용)")
        print("="*60)
        
        report = {}
        
        # 1. 레이더 차트 (5축)
        print("\n[1/4] 레이더 차트 계산 중...")
        report['radar_chart'] = self.calculate_radar_chart_v2(features)
        
        # 2. 음역대 분석
        print("\n[2/4] 음역대 분석 중...")
        report['vocal_range'] = self.analyze_vocal_range(features['pitch'])
        
        # 3. 고급 음색 프로필
        print("\n[3/4] 고급 음색 프로필 생성 중...")
        report['timbre_profile'] = self.analyze_timbre_advanced(features)
        
        # 4. 장르별 적합도
        print("\n[4/4] 장르별 적합도 계산 중...")
        report['genre_fitness'] = self.calculate_genre_fitness(
            features['pitch'],
            features['timbre'],
            report['radar_chart']
        )
        
        print("\n" + "="*60)
        print("✅ 리포트 생성 완료!")
        print("="*60 + "\n")
        
        return report
    
    # ========================================
    # 1. 레이더 차트 V2 (재설계)
    # ========================================
    
    def calculate_radar_chart_v2(self, features: Dict) -> Dict:
        """
        레이더 차트 5축 계산 (재설계)
        
        모든 점수는 0~100 범위, 높을수록 좋음
        
        1. 음정 안정도 (Pitch Stability)
           - F0 변동 계수 (각 음표 내)
           - 음정 급변 구간 비율
           - 음 이탈 구간 비율
           
        2. 리듬 안정도 (Rhythm Stability)
           - IOI 변동 계수
           - Tempo drift slope
           - Onset 에너지 일관성
           
        3. 강약 조절 (Dynamic Control)
           - 정규화된 다이나믹 범위 (연속형)
           - RMS 변화 부드러움 (연속형)
           - 가중 평균
           
        4. 발성 선명도 (Vocal Clarity)
           - HNR (Harmonics-to-Noise Ratio)
           - Spectral Flatness (역수)
           - Voiced 구간 에너지 안정성
           
        5. 고음 유지력 (High Note Stability)
           - 고음 구간 HNR 유지
           - 고음 구간 Flatness 증가 없음
           - 고음 구간 RMS 급락 없음
        
        Args:
            features: 전체 특징
        
        Returns:
            radar_scores: Dict
        """
        # 1. 음정 안정도 (개선)
        pitch_stability = self._calculate_pitch_stability_v2(features)
        
        # 2. 리듬 안정도 (개선)
        rhythm_stability = self._calculate_rhythm_stability_v2(features)
        
        # 3. 강약 조절 (개선 - 연속형)
        dynamic_control = self._calculate_dynamic_control_v2(features)
        
        # 4. 발성 선명도 (새로 추가)
        vocal_clarity = self._calculate_vocal_clarity(features)
        
        # 5. 고음 유지력 (새로 추가)
        high_note_stability = self._calculate_high_note_stability(features)
        
        print(f"✓ 레이더 차트 계산 완료")
        print(f"  - 음정 안정도: {pitch_stability:.1f}/100")
        print(f"  - 리듬 안정도: {rhythm_stability:.1f}/100")
        print(f"  - 강약 조절: {dynamic_control:.1f}/100")
        print(f"  - 발성 선명도: {vocal_clarity:.1f}/100")
        print(f"  - 고음 유지력: {high_note_stability:.1f}/100")
        
        # 각 메트릭에 대한 description 추가
        average_score = np.mean([
            pitch_stability,
            rhythm_stability,
            dynamic_control,
            vocal_clarity,
            high_note_stability
        ])
        
        return {
            'pitch_stability': pitch_stability,
            'rhythm_stability': rhythm_stability,
            'dynamic_control': dynamic_control,
            'vocal_clarity': vocal_clarity,
            'high_note_stability': high_note_stability,
            'average': average_score,
            # 각 메트릭에 대한 상세 설명 추가
            'descriptions': {
                'pitch_stability': {
                    'name': RADAR_CHART_DESCRIPTIONS['pitch_stability']['name'],
                    'short_desc': RADAR_CHART_DESCRIPTIONS['pitch_stability']['short_desc'],
                    'long_desc': RADAR_CHART_DESCRIPTIONS['pitch_stability']['long_desc'],
                    'high_example': RADAR_CHART_DESCRIPTIONS['pitch_stability']['high_example'],
                    'low_example': RADAR_CHART_DESCRIPTIONS['pitch_stability']['low_example'],
                    'measurement': RADAR_CHART_DESCRIPTIONS['pitch_stability']['measurement'],
                    'score': pitch_stability,
                    'interpretation': get_score_interpretation(pitch_stability)
                },
                'rhythm_stability': {
                    'name': RADAR_CHART_DESCRIPTIONS['rhythm_stability']['name'],
                    'short_desc': RADAR_CHART_DESCRIPTIONS['rhythm_stability']['short_desc'],
                    'long_desc': RADAR_CHART_DESCRIPTIONS['rhythm_stability']['long_desc'],
                    'high_example': RADAR_CHART_DESCRIPTIONS['rhythm_stability']['high_example'],
                    'low_example': RADAR_CHART_DESCRIPTIONS['rhythm_stability']['low_example'],
                    'measurement': RADAR_CHART_DESCRIPTIONS['rhythm_stability']['measurement'],
                    'score': rhythm_stability,
                    'interpretation': get_score_interpretation(rhythm_stability)
                },
                'dynamic_control': {
                    'name': RADAR_CHART_DESCRIPTIONS['dynamic_control']['name'],
                    'short_desc': RADAR_CHART_DESCRIPTIONS['dynamic_control']['short_desc'],
                    'long_desc': RADAR_CHART_DESCRIPTIONS['dynamic_control']['long_desc'],
                    'high_example': RADAR_CHART_DESCRIPTIONS['dynamic_control']['high_example'],
                    'low_example': RADAR_CHART_DESCRIPTIONS['dynamic_control']['low_example'],
                    'measurement': RADAR_CHART_DESCRIPTIONS['dynamic_control']['measurement'],
                    'score': dynamic_control,
                    'interpretation': get_score_interpretation(dynamic_control)
                },
                'vocal_clarity': {
                    'name': RADAR_CHART_DESCRIPTIONS['vocal_clarity']['name'],
                    'short_desc': RADAR_CHART_DESCRIPTIONS['vocal_clarity']['short_desc'],
                    'long_desc': RADAR_CHART_DESCRIPTIONS['vocal_clarity']['long_desc'],
                    'high_example': RADAR_CHART_DESCRIPTIONS['vocal_clarity']['high_example'],
                    'low_example': RADAR_CHART_DESCRIPTIONS['vocal_clarity']['low_example'],
                    'measurement': RADAR_CHART_DESCRIPTIONS['vocal_clarity']['measurement'],
                    'score': vocal_clarity,
                    'interpretation': get_score_interpretation(vocal_clarity)
                },
                'high_note_stability': {
                    'name': RADAR_CHART_DESCRIPTIONS['high_note_stability']['name'],
                    'short_desc': RADAR_CHART_DESCRIPTIONS['high_note_stability']['short_desc'],
                    'long_desc': RADAR_CHART_DESCRIPTIONS['high_note_stability']['long_desc'],
                    'high_example': RADAR_CHART_DESCRIPTIONS['high_note_stability']['high_example'],
                    'low_example': RADAR_CHART_DESCRIPTIONS['high_note_stability']['low_example'],
                    'measurement': RADAR_CHART_DESCRIPTIONS['high_note_stability']['measurement'],
                    'score': high_note_stability,
                    'interpretation': get_score_interpretation(high_note_stability)
                }
            }
        }
    
    def _calculate_pitch_stability_v2(self, features: Dict) -> float:
        """
        음정 안정도 (안정형 MVP)
        
        평가 기준:
        1. F0 변동 계수 (각 음표 내) - 60%
        2. 음정 급변 구간 비율 - 30%
        3. 음 이탈 구간 비율 - 10%
        
        목표 음정 없이도 측정 가능!
        """
        pitch_acc = features['pitch_accuracy']
        
        # 1. F0 안정성 (이미 계산됨)
        stability_score = pitch_acc['stability_score']  # 0~100
        
        # 2. 음정 급변 구간 비율
        # (이미 pitch_accuracy에서 계산됨)
        transition_smoothness = pitch_acc.get('transition_smoothness', 100.0)
        
        # 3. 음 이탈 구간 비율 (voiced ratio 기반)
        pitch_features = features['pitch']
        voiced_ratio = np.sum(pitch_features['voiced_mask']) / len(pitch_features['voiced_mask'])
        voiced_score = voiced_ratio * 100  # 0~1 → 0~100
        
        # 가중 평균
        final_score = stability_score * 0.6 + transition_smoothness * 0.3 + voiced_score * 0.1
        
        return float(final_score)
    
    def _calculate_rhythm_stability_v2(self, features: Dict) -> float:
        """
        리듬 안정도 (개선 - tempo drift 추가)
        
        평가 기준:
        1. IOI 변동 계수 - 70%
        2. Tempo drift - 30%
        """
        onset = features['onset']
        ioi_cv = onset['ioi_cv']
        
        # 1. IOI CV 점수
        if ioi_cv < 0.6:
            ioi_score = 100.0
        elif ioi_cv > 2.0:
            ioi_score = 0.0
        else:
            ioi_score = (1.0 - (ioi_cv - 0.6) / 1.4) * 100
        
        # 2. Tempo drift 점수
        # onset 시간에서 선형 회귀로 drift 측정
        onset_times = onset.get('onset_times', [])
        if len(onset_times) > 10:
            # 시간에 따른 IOI 변화
            iois = np.diff(onset_times)
            if len(iois) > 5:
                from scipy.stats import linregress
                x = np.arange(len(iois))
                slope, _, _, _, _ = linregress(x, iois)
                
                # slope가 0에 가까울수록 좋음
                # 절대값 0.01 이하 = 100점, 0.1 이상 = 0점
                drift_score = 100 - abs(slope) * 1000
                drift_score = np.clip(drift_score, 0, 100)
            else:
                drift_score = 100.0
        else:
            drift_score = 100.0
        
        # 가중 평균
        final_score = ioi_score * 0.7 + drift_score * 0.3
        
        return float(final_score)
    
    def _calculate_dynamic_control_v2(self, features: Dict) -> float:
        """
        강약 조절 (개선 - 연속형)
        
        평가 기준:
        1. 정규화된 다이나믹 범위 - 60%
        2. RMS 변화 부드러움 - 40%
        
        연속형 점수로 binary 문제 해결!
        """
        energy = features['energy']
        
        # 1. 다이나믹 범위 (연속형)
        rms_contour = np.array(energy['rms_contour'])
        rms_nonzero = rms_contour[rms_contour > 0]
        
        if len(rms_nonzero) < 10:
            return 0.0
        
        dynamic_range_db = 20 * np.log10(np.max(rms_nonzero) / (np.min(rms_nonzero) + 1e-6))
        
        # 연속형 정규화: 0dB = 0점, 15dB = 100점
        range_score = (dynamic_range_db / 15) * 100
        range_score = np.clip(range_score, 0, 100)
        
        # 2. RMS 변화 부드러움 (연속형)
        rms_diff = np.abs(np.diff(rms_nonzero))
        avg_diff = np.mean(rms_diff)
        
        # 연속형: 0 = 100점, 0.1 = 0점
        smoothness_score = 100 - (avg_diff * 1000)
        smoothness_score = np.clip(smoothness_score, 0, 100)
        
        # 가중 평균
        final_score = range_score * 0.6 + smoothness_score * 0.4
        
        return float(final_score)
    
    def _calculate_vocal_clarity(self, features: Dict) -> float:
        """
        발성 선명도 (개선 - 프레임 단위 HNR 직접 계산)
        
        평가 기준:
        1. HNR (Harmonics-to-Noise Ratio) - 40%
        2. Spectral Flatness 역수 - 30%
        3. Voiced 구간 에너지 안정성 - 30%
        
        개선점:
        - 세그먼트 평균이 아닌 프레임 단위 HNR 직접 계산
        - Voiced 구간만 필터링하여 정확도 향상
        """
        timbre = features['timbre']
        energy = features['energy']
        pitch = features['pitch']
        
        # 1. HNR (Clarity 값 사용 - 이미 0~1로 정규화됨)
        # timbre의 segment_stats에서 clarity 추출
        segment_stats = timbre['segment_stats']
        if segment_stats:
            clarity_values = []
            for seg in segment_stats:
                if 'clarity' in seg:
                    clarity_values.append(seg['clarity'])
            
            if clarity_values:
                avg_clarity = np.mean(clarity_values)
                # Clarity는 이미 0~1 범위로 정규화되어 있음
                hnr_score = avg_clarity * 100
                hnr_score = np.clip(hnr_score, 0, 100)
            else:
                hnr_score = 50.0
        else:
            hnr_score = 50.0
        
        # 2. Spectral Flatness 역수 (낮을수록 조화로움)
        if segment_stats:
            flatness_values = []
            for seg in segment_stats:
                if 'roughness' in seg:
                    flatness_values.append(seg['roughness'])
            
            if flatness_values:
                avg_flatness = np.mean(flatness_values)
                # Flatness가 낮을수록 좋음 (0 = 100점, 1 = 0점)
                flatness_score = (1 - avg_flatness) * 100
                flatness_score = np.clip(flatness_score, 0, 100)
            else:
                flatness_score = 50.0
        else:
            flatness_score = 50.0
        
        # 3. Voiced 구간 에너지 안정성
        voiced_mask = np.array(pitch['voiced_mask'])
        rms_contour = np.array(energy['rms_contour'])
        
        # Voiced 구간만 필터링
        if len(voiced_mask) == len(rms_contour):
            rms_voiced = rms_contour[voiced_mask]
            if len(rms_voiced) > 10:
                rms_cv = np.std(rms_voiced) / (np.mean(rms_voiced) + 1e-6)
                # CV가 낮을수록 안정적 (0 = 100점, 1 = 0점)
                energy_stability_score = 100 - (rms_cv * 100)
                energy_stability_score = np.clip(energy_stability_score, 0, 100)
            else:
                energy_stability_score = 50.0
        else:
            energy_stability_score = 50.0
        
        # 가중 평균
        final_score = hnr_score * 0.4 + flatness_score * 0.3 + energy_stability_score * 0.3
        
        return float(final_score)
    
    def _calculate_high_note_stability(self, features: Dict) -> float:
        """
        고음 유지력 (개선 - 프레임 단위 고음 구간 분석)
        
        평가 기준:
        1. 고음 구간 pitch 안정성 - 40%
        2. 고음 구간 HNR 유지 - 30%
        3. 고음 구간 에너지 유지 - 30%
        
        개선점:
        - 프레임 단위로 고음 구간 필터링
        - 고음 구간 내 안정성 직접 측정
        - Pitch std, HNR, RMS를 고음 구간에서만 계산
        """
        pitch = features['pitch']
        timbre = features['timbre']
        energy = features['energy']
        
        # 고음 구간 정의 (상위 25% F0)
        f0_contour = np.array(pitch['f0_contour'])
        voiced_mask = np.array(pitch['voiced_mask'])
        f0_voiced = f0_contour[voiced_mask]
        
        if len(f0_voiced) < 10:
            return 50.0
        
        # 고음 기준: 개인 최고음 기준 (더 공정함)
        # 최고음의 80% 이상을 "고음 구간"으로 정의
        f0_max = np.max(f0_voiced)
        f0_threshold = f0_max * 0.80  # 최고음의 80%
        
        # 최소 기준: 남성 C4 (261Hz), 여성 F4 (349Hz)
        f0_mean = np.mean(f0_voiced)
        if f0_mean < 200:  # 남성 (대략 G3 이하)
            min_threshold = 261.63  # C4
        else:  # 여성
            min_threshold = 349.23  # F4
        
        # 둘 중 높은 값 사용 (더 엄격하게)
        f0_threshold = max(f0_threshold, min_threshold)
        
        # 고음 구간 마스크
        high_note_mask = (f0_contour > f0_threshold) & voiced_mask
        
        if np.sum(high_note_mask) < 5:
            return 50.0  # 고음 구간이 없으면 중립 점수
        
        # 고음 구간 F0, RMS 추출
        f0_high = f0_contour[high_note_mask]
        rms_contour = np.array(energy['rms_contour'])
        
        # RMS 길이 맞추기
        if len(rms_contour) != len(f0_contour):
            # 보간하여 길이 맞춤
            from scipy.interpolate import interp1d
            x_old = np.linspace(0, 1, len(rms_contour))
            x_new = np.linspace(0, 1, len(f0_contour))
            f_interp = interp1d(x_old, rms_contour, kind='linear', fill_value='extrapolate')
            rms_contour = f_interp(x_new)
        
        rms_high = rms_contour[high_note_mask]
        
        # 1. 고음 구간 Pitch 안정성
        # 문제: 고음 구간 내에서 여러 음을 부르므로 std가 클 수밖에 없음
        # 해결: 고음 구간의 "평균 변동률"로 측정 (음표 간 변화가 아닌 프레임 간 변화)
        if len(f0_high) > 10:
            # 프레임 간 F0 변화율 (연속된 프레임 간 차이)
            f0_high_diff = np.abs(np.diff(f0_high))
            # 평균 변화율 (Hz 단위)
            avg_diff_hz = np.mean(f0_high_diff)
            # 평균 F0 대비 변화율 (%)
            avg_diff_ratio = avg_diff_hz / (np.mean(f0_high) + 1e-6)
            
            # 변화율이 낮을수록 안정적
            # 0% = 100점, 5% = 0점
            pitch_stability_score = 100 - (avg_diff_ratio * 100 / 5) * 100
            pitch_stability_score = np.clip(pitch_stability_score, 0, 100)
        else:
            pitch_stability_score = 50.0
        
        # 2. 고음 구간 HNR 유지 (Clarity 사용)
        # timbre segment_stats에서 고음 구간 clarity 추출
        segment_stats = timbre['segment_stats']
        high_clarity_values = []
        
        for seg in segment_stats:
            seg_f0_mean = seg.get('f0_mean', 0)
            if seg_f0_mean > f0_threshold and 'clarity' in seg:
                high_clarity_values.append(seg['clarity'])
        
        if high_clarity_values:
            avg_high_clarity = np.mean(high_clarity_values)
            # Clarity는 이미 0~1 범위
            hnr_score = avg_high_clarity * 100
            hnr_score = np.clip(hnr_score, 0, 100)
        else:
            hnr_score = 50.0
        
        # 3. 고음 구간 에너지 유지 (RMS 급락 없음)
        if len(rms_high) > 1:
            # RMS CV가 낮을수록 안정적
            rms_cv = np.std(rms_high) / (np.mean(rms_high) + 1e-6)
            # CV 0 = 100점, CV 1 = 0점
            energy_stability_score = 100 - (rms_cv * 100)
            energy_stability_score = np.clip(energy_stability_score, 0, 100)
        else:
            energy_stability_score = 50.0
        
        # 가중 평균
        final_score = pitch_stability_score * 0.4 + hnr_score * 0.3 + energy_stability_score * 0.3
        
        return float(final_score)
    
    # ========================================
    # 2. 음역대 분석
    # ========================================
    
    def analyze_vocal_range(self, pitch_features: Dict) -> Dict:
        """
        음역대 분석
        
        Args:
            pitch_features: Pitch 특징
        
        Returns:
            vocal_range: Dict
        """
        f0_min = pitch_features['f0_min']
        f0_max = pitch_features['f0_max']
        tessitura_low = pitch_features['tessitura_low']
        tessitura_high = pitch_features['tessitura_high']
        
        # Hz → Note 변환
        def hz_to_note(hz):
            if hz < 20:
                return "N/A"
            midi = librosa.hz_to_midi(hz)
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            octave = int(midi // 12) - 1
            note = note_names[int(midi % 12)]
            return f"{note}{octave}"
        
        # 음역대 (반음 수)
        if f0_min > 0 and f0_max > 0:
            range_semitones = 12 * np.log2(f0_max / f0_min)
        else:
            range_semitones = 0.0
        
        print(f"✓ 음역대 분석 완료")
        print(f"  - 최저음: {hz_to_note(f0_min)} ({f0_min:.1f}Hz)")
        print(f"  - 최고음: {hz_to_note(f0_max)} ({f0_max:.1f}Hz)")
        print(f"  - 테시투라: {hz_to_note(tessitura_low)} ~ {hz_to_note(tessitura_high)}")
        print(f"  - 음역대: {range_semitones:.1f} 반음")
        
        return {
            'lowest_hz': f0_min,
            'lowest_note': hz_to_note(f0_min),
            'highest_hz': f0_max,
            'highest_note': hz_to_note(f0_max),
            'tessitura_low_hz': tessitura_low,
            'tessitura_low_note': hz_to_note(tessitura_low),
            'tessitura_high_hz': tessitura_high,
            'tessitura_high_note': hz_to_note(tessitura_high),
            'range_semitones': float(range_semitones)
        }
    
    # ========================================
    # 3. 고급 음색 프로필
    # ========================================
    
    def analyze_timbre_advanced(self, features: Dict) -> Dict:
        """
        고급 음색 프로필 생성
        
        기존 5축 + MFCC 기반 특징 + Formant 특징
        
        Args:
            features: 전체 특징
        
        Returns:
            timbre_profile: Dict (brightness~warmth 각 항목에 raw `value` 유지 + `display_score` UI 보정 점수)
        """
        timbre = features['timbre']['weighted']
        advanced_timbre = features['advanced_timbre']
        
        # 기본 5축 (사용자용 axis_label + 5단계 interpretation + 청감 중심 description)
        profile = {
            'brightness': {
                'value': float(timbre['brightness']),
                'axis_label': '화사함·고역 존재감',
                'description': self._describe_brightness(timbre['brightness']),
                'interpretation': self._interpret_brightness(timbre['brightness'])
            },
            'roughness': {
                'value': float(timbre['roughness']),
                'axis_label': '거친 결·허스키 결',
                'description': self._describe_roughness(timbre['roughness']),
                'interpretation': self._interpret_roughness(timbre['roughness'])
            },
            'body': {
                'value': float(timbre['body']),
                'axis_label': '두께감·중심감',
                'description': self._describe_body(timbre['body']),
                'interpretation': self._interpret_body(timbre['body'])
            },
            'clarity': {
                'value': float(timbre['clarity']),
                'axis_label': '맑음·또렷함',
                'description': self._describe_clarity(timbre['clarity']),
                'interpretation': self._interpret_clarity(timbre['clarity'])
            },
            'warmth': {
                'value': float(timbre['warmth']),
                'axis_label': '온기·포근함',
                'description': self._describe_warmth(timbre['warmth']),
                'interpretation': self._interpret_warmth(timbre['warmth'])
            }
        }

        for axis_key in TIMBRE_DISPLAY_SCORE_RANGES:
            if axis_key in profile and isinstance(profile[axis_key], dict):
                profile[axis_key]["display_score"] = timbre_display_score_from_raw(
                    axis_key, profile[axis_key]["value"]
                )
        
        # MFCC 기반 보조 지표
        profile['richness'] = {
            'value': float(advanced_timbre['richness_mfcc']),
            'axis_label': '풍부함 (보조)',
            'description': self._describe_richness(advanced_timbre['richness_mfcc']),
            'interpretation': self._interpret_richness(advanced_timbre['richness_mfcc'])
        }
        
        profile['texture'] = {
            'value': float(advanced_timbre['texture_mfcc']),
            'axis_label': '질감 (보조)',
            'description': self._describe_texture(advanced_timbre['texture_mfcc']),
            'interpretation': self._interpret_texture(advanced_timbre['texture_mfcc'])
        }
        
        # Formant 정보
        profile['formants'] = {
            'f0_mean': float(timbre['f0_mean']),
            'f1': float(timbre['formant_f1']),
            'f2': float(timbre['formant_f2']),
            'description': self._describe_formants(timbre['formant_f1'], timbre['formant_f2'])
        }
        
        # 전체 요약
        summary = self._generate_timbre_summary_v2(profile)
        profile['summary'] = summary
        
        print(f"✓ 고급 음색 프로필 생성 완료")
        print(f"  {summary}")
        
        return profile

    def _describe_brightness(self, value: float) -> str:
        """고역 존재감·화사함 (한 축만으로 전체 음색을 단정하지 않음)."""
        if value < 0.16:
            return "고역이 많이 도드라지지 않아 차분하고 무게감 있게 들립니다."
        if value < 0.28:
            return "화사하게 뜨는 톤보다는 안정적이고 중심감 있는 인상이 있습니다."
        if value < 0.40:
            return "고역과 중역이 비교적 균형을 이루어 지나치게 밝거나 어둡지 않습니다."
        if value < 0.55:
            return "고역이 적절히 살아 있어 화사하고 청량한 인상을 줍니다."
        return "고역 존재감이 강해 매우 밝고 반짝이는 톤으로 들립니다."

    def _interpret_brightness(self, value: float) -> str:
        if value < 0.16:
            return self._TIER_5[0]
        if value < 0.28:
            return self._TIER_5[1]
        if value < 0.40:
            return self._TIER_5[2]
        if value < 0.55:
            return self._TIER_5[3]
        return self._TIER_5[4]

    def _describe_roughness(self, value: float) -> str:
        """거친 결·허스키 결 (값이 클수록 거침이 큼)."""
        if value < 0.05:
            return "잡음이 적고 매끈한 질감으로, 깨끗하고 부드럽게 들립니다."
        if value < 0.095:
            return "전반적으로 깔끔한 질감이며 거친 결은 크지 않습니다."
        if value < 0.16:
            return "약간의 질감 변화가 있어 개성이 느껴지지만 과하게 거칠지는 않습니다."
        if value < 0.24:
            return "소리에 거친 결이 느껴져 허스키하거나 날것의 인상이 일부 있습니다."
        return "거친 질감과 마찰감이 강하게 느껴지는 허스키한 톤입니다."

    def _interpret_roughness(self, value: float) -> str:
        if value < 0.05:
            return self._TIER_5[0]
        if value < 0.095:
            return self._TIER_5[1]
        if value < 0.16:
            return self._TIER_5[2]
        if value < 0.24:
            return self._TIER_5[3]
        return self._TIER_5[4]

    def _describe_body(self, value: float) -> str:
        """두께감·중심감."""
        if value < 0.22:
            return "소리가 가볍고 얇게 느껴지며 중심감은 비교적 적은 편입니다."
        if value < 0.38:
            return "무겁게 실리는 타입보다는 가볍고 경쾌한 인상이 있습니다."
        if value < 0.52:
            return "너무 얇지도 두껍지도 않아 균형 잡힌 중심감을 보입니다."
        if value < 0.68:
            return "중저역이 적절히 받쳐줘 소리에 두께감과 안정감이 느껴집니다."
        return "중심감이 강하고 소리의 두께가 뚜렷해 존재감 있게 들립니다."

    def _interpret_body(self, value: float) -> str:
        if value < 0.22:
            return self._TIER_5[0]
        if value < 0.38:
            return self._TIER_5[1]
        if value < 0.52:
            return self._TIER_5[2]
        if value < 0.68:
            return self._TIER_5[3]
        return self._TIER_5[4]

    def _describe_clarity(self, value: float) -> str:
        """맑음·또렷함 (밝음과는 별개로 설명)."""
        if value < 0.20:
            return "소리가 퍼지거나 흐릿하게 들려 선명도가 낮은 편입니다."
        if value < 0.38:
            return "또렷함보다는 부드럽고 퍼지는 인상이 조금 더 느껴집니다."
        if value < 0.52:
            return "전반적으로 무난한 선명도를 보이며 과하게 흐리거나 날카롭지 않습니다."
        if value < 0.68:
            return "소리가 비교적 또렷하고 맑게 들려 전달력이 좋습니다."
        return "매우 선명하고 투명한 톤으로, 소리의 윤곽이 뚜렷하게 들립니다."

    def _interpret_clarity(self, value: float) -> str:
        if value < 0.20:
            return self._TIER_5[0]
        if value < 0.38:
            return self._TIER_5[1]
        if value < 0.52:
            return self._TIER_5[2]
        if value < 0.68:
            return self._TIER_5[3]
        return self._TIER_5[4]

    def _describe_warmth(self, value: float) -> str:
        """온기·포근함."""
        if value < 0.22:
            return "온기보다는 차갑고 또렷한 인상이 상대적으로 강합니다."
        if value < 0.36:
            return "따뜻함보다는 비교적 담백하고 시원한 인상에 가깝습니다."
        if value < 0.5:
            return "차갑거나 과하게 따뜻하지 않은 중립적인 온도감입니다."
        if value < 0.64:
            return "중저역의 온기가 느껴져 부드럽고 편안한 인상을 줍니다."
        return "포근하고 따뜻한 울림이 뚜렷한 톤입니다."

    def _interpret_warmth(self, value: float) -> str:
        if value < 0.22:
            return self._TIER_5[0]
        if value < 0.36:
            return self._TIER_5[1]
        if value < 0.5:
            return self._TIER_5[2]
        if value < 0.64:
            return self._TIER_5[3]
        return self._TIER_5[4]

    def _describe_richness(self, value: float) -> str:
        """보조: 음색 겹겹이 쌓인 느낌."""
        if value < 0.3:
            return "단순하고 깔끔한 음색"
        if value < 0.6:
            return "적당히 풍부한 음색"
        return "여러 결이 겹쳐 느껴지는 풍부한 음색"

    def _interpret_richness(self, value: float) -> str:
        if value < 0.3:
            return "낮음"
        if value < 0.6:
            return "중간"
        return "높음"

    def _describe_texture(self, value: float) -> str:
        """보조: 질감 변화."""
        if value < 0.3:
            return "매끈하고 일관된 질감"
        if value < 0.6:
            return "약간의 변화가 느껴지는 질감"
        return "결의 변화가 비교적 뚜렷하고 질감이 입체적으로 느껴집니다."

    def _interpret_texture(self, value: float) -> str:
        if value < 0.3:
            return "낮음"
        if value < 0.6:
            return "중간"
        return "높음"
    
    def _describe_formants(self, f1: float, f2: float) -> str:
        """Formant 기반 공명 경향 (한 축으로 전체 톤을 단정하지 않음)."""
        if f1 < 500:
            f1_desc = "고역 쪽 공명이 비교적 살아 있는"
        elif f1 < 650:
            f1_desc = "개방감이 중간 정도인"
        else:
            f1_desc = "깊게 잡히는 저·중공명이 느껴지는"
        
        if f2 < 1400:
            f2_desc = "후방 쪽 울림"
        elif f2 < 1800:
            f2_desc = "중앙 쪽 울림"
        else:
            f2_desc = "전방 쪽 울림"
        
        return f"{f1_desc}, {f2_desc}"
    
    def _generate_timbre_summary_v2(self, profile: Dict) -> str:
        """축 이름 나열 대신 청감 중심 문장 1~2개로 요약 (한 축만으로 단정하지 않음)."""

        def intr(key: str) -> str:
            return (profile.get(key) or {}).get('interpretation', '중간')

        r_rough = intr('roughness')
        r_bright = intr('brightness')
        r_body = intr('body')
        r_clarity = intr('clarity')
        r_warmth = intr('warmth')

        # --- 첫 문장: 거침 + 화사함/중심감(톤) ---
        if r_rough in ('매우 낮음', '낮은 편'):
            head = "전반적으로 거친 결이 적고, "
        elif r_rough in ('높은 편', '매우 높음'):
            head = "거친 결이나 허스키한 질감이 비교적 뚜렷하게 느껴지며, "
        else:
            head = ""

        if r_bright in ('매우 낮음', '낮은 편'):
            tail = "화사하게 뜨기보다는 차분하고 중심감 있는 톤으로 들립니다."
        elif r_bright == '중간':
            if r_body in ('높은 편', '매우 높음'):
                tail = "두께감과 중심감이 함께 받쳐 주는 듯한 톤이 느껴집니다."
            elif r_body in ('매우 낮음', '낮은 편'):
                tail = "가볍고 경쾌한 쪽에 가까운 톤으로 들립니다."
            else:
                tail = "고역과 무게감의 균형이 무난한 톤으로 들립니다."
        elif r_bright in ('높은 편', '매우 높음'):
            tail = "고역이 살아 있어 화사하고 청량한 인상의 톤입니다."
        else:
            tail = "여러 요소가 한쪽으로 치우치지 않은 편으로 들립니다."

        if not head and tail.startswith("여러 요소"):
            sentence1 = tail
        elif not head:
            sentence1 = tail
        else:
            sentence1 = head + tail

        # --- 둘째 문장: 선명도 + 온기 (~이며, ~입니다.) ---
        if r_clarity in ('높은 편', '매우 높음'):
            c_part = "맑고 또렷한 인상이 비교적 강하"
        elif r_clarity in ('매우 낮음', '낮은 편'):
            c_part = "소리가 다소 퍼지거나 부드럽게 들리는 편이"
        else:
            c_part = "선명도는 무난한 편이"

        if r_warmth == '중간':
            w_part = "온기는 과하지 않은 중립적인 편입니다"
        elif r_warmth in ('매우 낮음', '낮은 편'):
            w_part = "온기보다는 담백하고 시원한 인상에 가깝습니다"
        elif r_warmth in ('높은 편', '매우 높음'):
            w_part = "중저역의 온기나 포근함이 함께 느껴집니다"
        else:
            w_part = "온도감은 무난한 편입니다"

        sentence2 = f"{c_part}며, {w_part}."

        summary = sentence1 + " " + sentence2

        # 보조: 짧게 덧붙임 (나열·비문 피함)
        aux_tail = []
        if profile.get('richness', {}).get('interpretation') == '높음':
            aux_tail.append("겹겹이 쌓인 듯한 풍부함이 살짝 느껴집니다")
        if profile.get('texture', {}).get('interpretation') == '높음':
            aux_tail.append("결의 변화가 비교적 뚜렷하게 느껴집니다")
        if aux_tail:
            summary += " " + ". ".join(aux_tail) + "."

        return summary
    
    # ========================================
    # 4. 장르별 적합도
    # ========================================
    
    def calculate_genre_fitness(
        self,
        pitch_features: Dict,
        timbre_features: Dict,
        radar_chart: Dict
    ) -> Dict:
        """
        장르별 적합도 계산
        
        유저의 음역대, 음색, 발성 스타일을 각 장르의 특성과 비교하여
        어떤 장르에 가장 적합한지 점수화
        
        Args:
            pitch_features: Pitch 특징
            timbre_features: Timbre 특징
            radar_chart: 레이더 차트 점수
        
        Returns:
            genre_fitness: {
                'scores': {
                    '발라드': 85.3,
                    'POP': 78.2,
                    ...
                },
                'top_genres': [
                    {
                        'genre': '발라드',
                        'score': 85.3,
                        'reason': '...'
                    },
                    ...
                ],
                'analysis': {...}
            }
        """
        from genre_profiles import (
            GENRE_PROFILES,
            calculate_pitch_distance,
            calculate_timbre_distance,
            calculate_vocal_style_distance
        )
        
        # 유저 데이터 준비
        user_pitch = {
            'tessitura_low': pitch_features['tessitura_low'],
            'tessitura_high': pitch_features['tessitura_high'],
            'range_semitones': 12 * np.log2(
                pitch_features['f0_max'] / pitch_features['f0_min']
            ) if pitch_features['f0_min'] > 0 else 24.0
        }
        
        user_timbre = timbre_features['weighted']
        
        # 각 장르별 적합도 계산
        genre_scores = {}
        genre_details = {}
        
        for genre_name, genre_profile in GENRE_PROFILES.items():
            # 1. 음역대 거리
            pitch_dist = calculate_pitch_distance(
                user_pitch,
                genre_profile['pitch']
            )
            
            # 2. 음색 거리
            timbre_dist = calculate_timbre_distance(
                user_timbre,
                genre_profile['timbre']
            )
            
            # 3. 발성 스타일 거리
            vocal_dist = calculate_vocal_style_distance(
                radar_chart,
                genre_profile['vocal_style']
            )
            
            # 가중 평균으로 최종 거리 계산
            weights = genre_profile['weights']
            total_distance = (
                pitch_dist * weights['pitch'] +
                timbre_dist * weights['timbre'] +
                vocal_dist * weights['vocal_style']
            )
            
            # 거리 → 점수 변환 (0~100)
            # 거리가 0이면 100점, 거리가 1이면 0점
            score = (1.0 - total_distance) * 100
            
            genre_scores[genre_name] = float(score)
            genre_details[genre_name] = {
                'pitch_distance': float(pitch_dist),
                'timbre_distance': float(timbre_dist),
                'vocal_distance': float(vocal_dist),
                'total_distance': float(total_distance)
            }
        
        # 상위 3개 장르 추출
        sorted_genres = sorted(
            genre_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        top_genres = []
        for genre_name, score in sorted_genres[:3]:
            reason = self._generate_genre_reason(
                genre_name,
                genre_details[genre_name],
                user_pitch,
                user_timbre
            )
            
            top_genres.append({
                'genre': genre_name,
                'score': score,
                'description': GENRE_PROFILES[genre_name]['description'],
                'reason': reason
            })
        
        print(f"✓ 장르별 적합도 계산 완료")
        for item in top_genres:
            print(f"  - {item['genre']}: {item['score']:.1f}/100")
        
        return {
            'scores': genre_scores,
            'top_genres': top_genres,
            'analysis': {
                'best_match': sorted_genres[0][0],
                'best_score': sorted_genres[0][1],
                'details': genre_details
            }
        }
    
    def _generate_genre_reason(
        self,
        genre_name: str,
        distances: Dict,
        user_pitch: Dict,
        user_timbre: Dict
    ) -> str:
        """장르 적합도 이유 생성"""
        from genre_profiles import GENRE_PROFILES
        
        genre_profile = GENRE_PROFILES[genre_name]
        reasons = []
        
        # 음역대 분석
        if distances['pitch_distance'] < 0.3:
            reasons.append("음역대가 잘 맞음")
        elif distances['pitch_distance'] > 0.7:
            reasons.append("음역대 차이가 있음")
        
        # 음색 분석
        if distances['timbre_distance'] < 0.3:
            # 어떤 음색 축이 비슷한지 찾기
            similar_axes = []
            genre_timbre = genre_profile['timbre']
            
            for axis in ['brightness', 'warmth', 'body']:
                diff = abs(user_timbre[axis] - genre_timbre[axis])
                if diff < 0.2:
                    axis_names = {
                        'brightness': '밝기',
                        'warmth': '따뜻함',
                        'body': '바디감'
                    }
                    similar_axes.append(axis_names[axis])
            
            if similar_axes:
                reasons.append(f"음색이 유사함 ({', '.join(similar_axes)})")
        
        # 발성 스타일 분석
        if distances['vocal_distance'] < 0.3:
            reasons.append("발성 스타일이 적합함")
        
        # 이유가 없으면 기본 메시지
        if not reasons:
            if distances['total_distance'] < 0.5:
                reasons.append("전반적으로 적합함")
            else:
                reasons.append("일부 특성이 맞음")
        
        return ", ".join(reasons)


"""
보컬 분석 리포트 상세 테스트 스크립트
- 전체 리포트 구조 확인
- 각 요소별 측정 방법 확인
- 점수 해석 확인
"""
import sys
from pathlib import Path
import json

# 상위 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent))

from user_vocal_pipeline import UserVocalPipeline
from radar_chart_descriptions import (
    RADAR_CHART_DESCRIPTIONS,
    get_score_interpretation,
    get_detailed_feedback
)


def print_section(title: str, width: int = 70):
    """섹션 제목 출력"""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def test_radar_chart_detailed(report: dict):
    """레이더 차트 상세 분석"""
    print_section("📊 레이더 차트 상세 분석")
    
    radar = report['radar_chart']
    descriptions = radar['descriptions']
    
    metrics = [
        ('pitch_stability', '🎯', '음정 안정도'),
        ('rhythm_stability', '🎵', '리듬 안정도'),
        ('dynamic_control', '📊', '강약 조절'),
        ('vocal_clarity', '💎', '발성 선명도'),
        ('high_note_stability', '🎤', '고음 유지력')
    ]
    
    for metric_key, emoji, name in metrics:
        desc = descriptions[metric_key]
        score = desc['score']
        interpretation = desc['interpretation']
        
        print(f"\n{emoji} {name}: {score:.1f}/100 ({interpretation})")
        print(f"   └─ 짧은 설명: {desc['short_desc']}")
        print(f"   └─ 긴 설명: {desc['long_desc']}")
        print(f"   └─ 측정 방법: {desc['measurement']}")
        print(f"   └─ 높은 점수 예시: {desc['high_example']}")
        print(f"   └─ 낮은 점수 예시: {desc['low_example']}")
        
        # 피드백
        feedback = get_detailed_feedback(metric_key, score)
        print(f"   └─ 피드백: {feedback}")
    
    print(f"\n⭐ 평균 점수: {radar['average']:.1f}/100 ({get_score_interpretation(radar['average'])})")


def test_vocal_range(report: dict):
    """음역대 분석"""
    print_section("🎵 음역대 분석")
    
    vr = report['vocal_range']
    
    print(f"최저음: {vr['lowest_note']} ({vr['lowest_hz']:.1f}Hz)")
    print(f"최고음: {vr['highest_note']} ({vr['highest_hz']:.1f}Hz)")
    print(f"테시투라: {vr['tessitura_low_note']} ~ {vr['tessitura_high_note']}")
    print(f"  └─ {vr['tessitura_low_hz']:.1f}Hz ~ {vr['tessitura_high_hz']:.1f}Hz")
    print(f"음역대: {vr['range_semitones']:.1f} 반음")
    
    # 음역대 평가
    if vr['range_semitones'] >= 24:
        print("   └─ 평가: 넓은 음역대 (2옥타브 이상)")
    elif vr['range_semitones'] >= 18:
        print("   └─ 평가: 적당한 음역대 (1.5옥타브 이상)")
    else:
        print("   └─ 평가: 좁은 음역대 (1.5옥타브 미만)")


def test_timbre_profile(report: dict):
    """음색 프로파일 분석"""
    print_section("🎨 음색 프로파일 분석")
    
    timbre = report['timbre_profile']
    
    # 전체 요약
    if 'summary' in timbre:
        print(f"전체 요약: {timbre['summary']}\n")
    
    # 각 축별 상세 분석
    timbre_axes = [
        ('brightness', '밝기'),
        ('roughness', '거칠음'),
        ('body', '바디'),
        ('clarity', '선명도'),
        ('warmth', '따뜻함'),
        ('richness', '풍부함'),
        ('texture', '질감')
    ]
    
    for key, name in timbre_axes:
        if key in timbre:
            value = timbre[key]
            # value가 dict인 경우와 아닌 경우 모두 처리
            if isinstance(value, dict):
                if 'value' in value:
                    val = value['value']
                    desc = value.get('description', '')
                    interp = value.get('interpretation', '')
                    
                    print(f"{name}: {val:.3f}")
                    if interp:
                        print(f"   └─ 해석: {interp}")
                    if desc:
                        print(f"   └─ 설명: {desc}")
                    print()
                elif 'description' in value:
                    # value가 dict이지만 'value' 키가 없는 경우
                    desc = value.get('description', '')
                    interp = value.get('interpretation', '')
                    print(f"{name}")
                    if interp:
                        print(f"   └─ 해석: {interp}")
                    if desc:
                        print(f"   └─ 설명: {desc}")
                    print()
            elif isinstance(value, (int, float)):
                # value가 숫자인 경우
                print(f"{name}: {value:.3f}")
                print()
    
    # Formant 정보
    if 'formants' in timbre:
        formants = timbre['formants']
        print(f"📊 Formant 정보:")
        print(f"   └─ F0 평균: {formants.get('f0_mean', 0):.1f}Hz")
        print(f"   └─ F1: {formants.get('f1', 0):.1f}Hz")
        print(f"   └─ F2: {formants.get('f2', 0):.1f}Hz")
        if 'description' in formants:
            print(f"   └─ 설명: {formants['description']}")


def test_vocal_technique(report: dict):
    """발성 기술 분석"""
    print_section("🎤 발성 기술 분석")
    
    tech = report['vocal_technique']
    
    print(f"음역대: {tech['register']}")
    print(f"사용 기술: {', '.join(tech['techniques_used']) if tech['techniques_used'] else '기본 발성'}")
    
    if tech['techniques_used']:
        print("\n기술별 점수:")
        for technique, score in tech['technique_scores'].items():
            if score > 0:
                print(f"   └─ {technique}: {score:.1f}/100")
    
    print(f"\n배음 강도: {tech['harmonic_strength']:.3f}")
    print(f"기식성: {tech['breathiness']:.3f}")
    print(f"공명 품질: {tech['resonance_quality']:.1f}/100")
    print(f"전체 기술 점수: {tech['overall_score']:.1f}/100")


def test_vibrato_analysis(report: dict):
    """비브라토 분석"""
    print_section("🎵 비브라토 분석")
    
    vibrato = report['vibrato_analysis']
    
    if vibrato['has_vibrato']:
        print("✅ 비브라토 사용")
        print(f"   └─ 속도: {vibrato['rate_hz']:.2f}Hz (이상적: 5-7Hz)")
        print(f"   └─ 폭: {vibrato['extent_cents']:.1f} cents (이상적: 50-100 cents)")
        print(f"   └─ 규칙성: {vibrato['regularity']:.3f} (높을수록 규칙적)")
        print(f"   └─ 강도: {vibrato['strength']:.3f}")
        print(f"   └─ 전체 점수: {vibrato['overall_score']:.1f}/100")
        
        # 평가
        rate_score = vibrato['rate_score']
        extent_score = vibrato['extent_score']
        regularity_score = vibrato['regularity_score']
        
        print(f"\n   세부 점수:")
        print(f"   └─ 속도 점수: {rate_score:.1f}/100")
        print(f"   └─ 폭 점수: {extent_score:.1f}/100")
        print(f"   └─ 규칙성 점수: {regularity_score:.1f}/100")
    else:
        print("❌ 비브라토 미사용")


def print_measurement_details():
    """측정 방법 상세 설명"""
    print_section("🔬 각 요소 측정 방법 상세")
    
    print("\n1. 음정 안정도 (Pitch Stability)")
    print("   └─ 측정 지표:")
    print("      • F0 변동 계수 (각 음표 내) - 60%")
    print("        → 각 음표 내에서 F0의 표준편차를 cent 단위로 계산")
    print("        → 20 cent 이하 = 100점, 80 cent 이상 = 0점")
    print("      • 음정 급변 구간 비율 - 30%")
    print("        → 음정 전환 시 부드러움 측정")
    print("      • 음 이탈 구간 비율 - 10%")
    print("        → voiced_mask 기반 유성음 비율")
    
    print("\n2. 리듬 안정도 (Rhythm Stability)")
    print("   └─ 측정 지표:")
    print("      • IOI 변동 계수 - 70%")
    print("        → Onset 간격(IOI)의 변동 계수(CV) 계산")
    print("        → CV < 0.6 = 100점, CV > 2.0 = 0점")
    print("      • Tempo drift - 30%")
    print("        → 시간에 따른 IOI 변화를 선형 회귀로 측정")
    print("        → slope가 0에 가까울수록 좋음")
    
    print("\n3. 강약 조절 (Dynamic Control)")
    print("   └─ 측정 지표:")
    print("      • 정규화된 다이나믹 범위 - 60%")
    print("        → RMS 최대값/최소값의 dB 차이")
    print("        → 0dB = 0점, 15dB = 100점")
    print("      • RMS 변화 부드러움 - 40%")
    print("        → RMS 변화량의 평균")
    print("        → 0 = 100점, 0.1 = 0점")
    
    print("\n4. 발성 선명도 (Vocal Clarity)")
    print("   └─ 측정 지표:")
    print("      • HNR (Harmonics-to-Noise Ratio) - 40%")
    print("        → 조화음과 잡음의 비율")
    print("      • Spectral Flatness 역수 - 30%")
    print("        → 낮을수록 조화로움")
    print("      • Voiced 구간 에너지 안정성 - 30%")
    print("        → voiced_mask로 필터링한 RMS의 변동 계수")
    
    print("\n5. 고음 유지력 (High Note Stability)")
    print("   └─ 측정 지표:")
    print("      • 고음 구간 정의:")
    print("        → 개인 최고음의 80% 이상")
    print("        → 최소 기준: 남성 C4 (261Hz), 여성 F4 (349Hz)")
    print("      • 고음 구간 Pitch 안정성 - 40%")
    print("        → 프레임 간 F0 변화율")
    print("        → 0% = 100점, 5% = 0점")
    print("      • 고음 구간 HNR 유지 - 30%")
    print("        → 고음 구간의 clarity 값 평균")
    print("      • 고음 구간 에너지 유지 - 30%")
    print("        → 고음 구간 RMS의 변동 계수")


def print_element_selection_process():
    """요소 선정 과정 설명"""
    print_section("📋 5개 요소 선정 과정 및 이유")
    
    print("\n[기존 요소들의 한계점]")
    print("\n1. 음정 정확도 (Pitch Accuracy)")
    print("   └─ 한계: MR(반주)이 필요함 → 아카펠라만으로는 측정 불가능")
    print("   └─ 해결: 음정 안정도로 대체 (MR 없이도 측정 가능)")
    
    print("\n2. 리듬 정확도 (Rhythm Accuracy)")
    print("   └─ 한계: MR 박자와 비교 필요 → 아카펠라만으로는 측정 불가능")
    print("   └─ 해결: 리듬 안정도로 대체 (자기 템포 일정성 측정)")
    
    print("\n3. 호흡 조절 (Breath Control)")
    print("   └─ 한계: 직접 측정이 어려움 (간접 지표만 가능)")
    print("   └─ 해결: 강약 조절로 통합 (다이나믹 범위 + 부드러움)")
    
    print("\n4. 음색 (Timbre)")
    print("   └─ 한계: 레이더 차트에 포함하기엔 너무 복잡 (5차원)")
    print("   └─ 해결: 별도 섹션으로 분리 (timbre_profile)")
    
    print("\n5. 음역대 (Vocal Range)")
    print("   └─ 한계: 레이더 차트에 포함하기엔 부적합 (범위 정보)")
    print("   └─ 해결: 별도 섹션으로 분리 (vocal_range)")
    
    print("\n[5개 요소로 결정하기까지의 과정]")
    print("\nStep 1: 안정형 MVP 설계")
    print("   └─ 목표: MR 없이도 측정 가능한 순수 보컬 품질 지표")
    print("   └─ 원칙:")
    print("      • 목표 음정/박자 없이도 측정 가능")
    print("      • 연속형 점수 (0~100)")
    print("      • 유저가 이해하기 쉬운 개념")
    
    print("\nStep 2: 요소 후보 선정")
    print("   1. ✅ 음정 안정도: F0 변동 계수로 측정 가능")
    print("   2. ✅ 리듬 안정도: IOI 변동 계수로 측정 가능")
    print("   3. ✅ 강약 조절: RMS 다이나믹 범위로 측정 가능")
    print("   4. ✅ 발성 선명도: HNR로 측정 가능")
    print("   5. ✅ 고음 유지력: 고음 구간 안정성으로 측정 가능")
    
    print("\nStep 3: 요소 검증")
    print("   └─ 각 요소가 독립적인가? ✅")
    print("   └─ 측정 가능한가? ✅")
    print("   └─ 유저가 이해할 수 있는가? ✅")
    print("   └─ 개선 가능한가? ✅")
    
    print("\nStep 4: 최종 확정")
    print("   └─ 5개 요소로 결정 (너무 많으면 복잡, 너무 적으면 부족)")
    print("   └─ 각 요소별 가중치 조정")
    print("   └─ 설명 텍스트 작성")


def main():
    """메인 함수"""
    print("\n" + "=" * 70)
    print("  🎤 보컬 분석 리포트 상세 테스트")
    print("=" * 70)
    
    # CLI 인자 확인
    if len(sys.argv) < 2:
        print("\n사용법: python test_report_detailed.py <audio_file_path>")
        print("\n또는 상세 설명만 보기:")
        print("  python test_report_detailed.py --info")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    # 정보만 출력하는 경우
    if audio_path == "--info":
        print_measurement_details()
        print_element_selection_process()
        return
    
    # 파일 존재 확인
    if not Path(audio_path).exists():
        print(f"\n❌ 파일을 찾을 수 없습니다: {audio_path}")
        sys.exit(1)
    
    # 파이프라인 실행
    print(f"\n📁 분석할 파일: {audio_path}")
    print("⏳ 분석 중... (수 분 소요될 수 있습니다)\n")
    
    try:
        # 빠른 모드 활성화 (속도 최적화)
        pipeline = UserVocalPipeline(fast_mode=True)
        result = pipeline.process(
            audio_path=audio_path,
            output_dir="./test_output",
            save_features=False  # 특징 저장 비활성화로 속도 향상
        )
        
        report = result['report']
        
        # 상세 분석 출력
        test_radar_chart_detailed(report)
        test_vocal_range(report)
        test_timbre_profile(report)
        
        # 발성 기술 및 비브라토 분석은 제외됨
        # test_vocal_technique(report)
        # test_vibrato_analysis(report)
        
        # 측정 방법 설명
        print_measurement_details()
        
        # 요소 선정 과정 설명
        print_element_selection_process()
        
        # JSON 저장 위치
        print_section("💾 결과 저장")
        print(f"전체 리포트가 JSON 파일로 저장되었습니다.")
        print(f"파일 위치: ./test_output/{Path(audio_path).stem}_result.json")
        
        print("\n✅ 분석 완료!")
        
    except Exception as e:
        print(f"\n❌ 분석 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


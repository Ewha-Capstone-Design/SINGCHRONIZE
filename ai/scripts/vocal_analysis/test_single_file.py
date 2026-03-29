#!/usr/bin/env python3
"""
단일 파일 테스트 스크립트 (아카펠라 전용)
"""
import sys
from pathlib import Path

# vocal_analysis 폴더를 path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from user_vocal_pipeline import UserVocalPipeline

def main():
    print("=" * 60)
    print("🎤 SINGCHRONIZE 보컬 분석 테스트 (아카펠라 전용)")
    print("=" * 60)
    print("⚠️  주의: 반드시 아카펠라 녹음 파일을 사용하세요!")
    print("=" * 60)
    
    # 파일 경로 (ai/ 디렉토리 기준)
    audio_file = "../../test_data/test1.m4a"
    output_dir = "test_output"
    
    # 파일 존재 확인
    if not Path(audio_file).exists():
        print(f"❌ 파일이 없습니다: {audio_file}")
        return
    
    print(f"\n📁 입력 파일: {audio_file}")
    print(f"📁 출력 폴더: {output_dir}")
    
    # 파이프라인 실행 (아카펠라 전용)
    try:
        pipeline = UserVocalPipeline()
        result = pipeline.process(audio_file, output_dir)
        
        print("\n" + "=" * 60)
        print("✅ 테스트 완료!")
        print("=" * 60)
        print(f"\n📊 결과 파일: {output_dir}/test1_result.json")
        
        # 레이더 차트 점수 출력
        print("\n[레이더 차트 점수]")
        radar = result['report']['radar_chart']
        print(f"  🎯 음정 안정도: {radar['pitch_stability']:.1f}/100")
        print(f"  🎵 리듬 안정도: {radar['rhythm_stability']:.1f}/100")
        print(f"  📊 강약 조절: {radar['dynamic_control']:.1f}/100")
        print(f"  💎 발성 선명도: {radar['vocal_clarity']:.1f}/100")
        print(f"  🎤 고음 유지력: {radar['high_note_stability']:.1f}/100")
        print(f"  ⭐ 평균: {radar['average']:.1f}/100")
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()



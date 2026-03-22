#!/usr/bin/env python3
"""
빠른 보컬 분석 테스트 스크립트 (속도 최적화)
- 빠른 모드 활성화
- 특징 저장 비활성화
- ECAPA 임베딩 최적화 (상위 3개 세그먼트만 사용)
"""
import sys
from pathlib import Path
import json

# 상위 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent))

from user_vocal_pipeline import UserVocalPipeline


def main():
    """빠른 테스트 실행"""
    print("\n" + "=" * 70)
    print("  🚀 빠른 보컬 분석 테스트 (속도 최적화)")
    print("=" * 70)
    
    # CLI 인자 확인
    if len(sys.argv) < 2:
        print("\n사용법: python test_fast.py <audio_file_path>")
        print("\n예시:")
        print("  python test_fast.py ../../test_data/test1.m4a")
        print("  python test_fast.py ../../test_data/test2.m4a")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    # 파일 존재 확인
    if not Path(audio_path).exists():
        print(f"\n❌ 파일을 찾을 수 없습니다: {audio_path}")
        sys.exit(1)
    
    # 파이프라인 실행 (빠른 모드)
    print(f"\n📁 분석할 파일: {audio_path}")
    print("⚡ 빠른 모드 활성화:")
    print("  - 세그먼트 길이: 30초 (기본 20초)")
    print("  - 세그먼트 간격: 15초 (기본 5초)")
    print("  - ECAPA 임베딩: 상위 3개 세그먼트만 사용")
    print("  - 특징 저장: 비활성화")
    print("\n⏳ 분석 중...\n")
    
    try:
        import time
        start_time = time.time()
        
        # 빠른 모드 파이프라인
        pipeline = UserVocalPipeline(fast_mode=True)
        result = pipeline.process(
            audio_path=audio_path,
            output_dir="./test_output",
            save_features=False  # 특징 저장 비활성화
        )
        
        elapsed_time = time.time() - start_time
        
        # JSON 저장 위치
        output_file = Path("./test_output") / f"{Path(audio_path).stem}_result.json"
        
        print("\n" + "=" * 70)
        print("✅ 분석 완료!")
        print("=" * 70)
        print(f"⏱️  소요 시간: {elapsed_time:.1f}초 ({elapsed_time/60:.1f}분)")
        print(f"📁 결과 파일: {output_file}")
        
        # 레이더 차트 요약
        print("\n[레이더 차트 점수]")
        radar = result['report']['radar_chart']
        print(f"  🎯 음정 안정도: {radar['pitch_stability']:.1f}/100")
        print(f"  🎵 리듬 안정도: {radar['rhythm_stability']:.1f}/100")
        print(f"  📊 강약 조절: {radar['dynamic_control']:.1f}/100")
        print(f"  💎 발성 선명도: {radar['vocal_clarity']:.1f}/100")
        print(f"  🎤 고음 유지력: {radar['high_note_stability']:.1f}/100")
        print(f"  ⭐ 평균: {radar['average']:.1f}/100")
        
        print("\n" + "=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ 분석 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()






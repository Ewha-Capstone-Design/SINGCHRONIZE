#!/usr/bin/env python3
"""
워커 테스트 스크립트

현재는 로컬 파일로 테스트
나중에 AWS 연결 후에는 실제 S3 + DB 사용
"""
import sys
from pathlib import Path

# vocal_analysis 폴더를 path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from vocal_analysis_worker import VocalAnalysisWorker, test_single_job, test_batch_jobs


def test_single():
    """단일 작업 테스트"""
    print("="*70)
    print("🧪 단일 작업 테스트")
    print("="*70)
    
    result = test_single_job(
        job_id="test_job_001",
        audio_path="../../test_data/test2.m4a"
    )
    
    if result['status'] == 'success':
        print("\n📊 분석 결과 요약:")
        radar = result['result']['report']['radar_chart']
        print(f"  🎯 음정 안정도: {radar['pitch_stability']:.1f}/100")
        print(f"  🎵 리듬 안정도: {radar['rhythm_stability']:.1f}/100")
        print(f"  📊 강약 조절: {radar['dynamic_control']:.1f}/100")
        print(f"  💎 발성 선명도: {radar['vocal_clarity']:.1f}/100")
        print(f"  🎤 고음 유지력: {radar['high_note_stability']:.1f}/100")
        print(f"  ⭐ 평균: {radar['average']:.1f}/100")


def test_batch():
    """배치 작업 테스트"""
    print("="*70)
    print("🧪 배치 작업 테스트")
    print("="*70)
    
    jobs = [
        {
            'job_id': 'batch_job_001',
            'audio_path': '../../test_data/test1.m4a'
        },
        {
            'job_id': 'batch_job_002',
            'audio_path': '../../test_data/test2.m4a'
        }
    ]
    
    results = test_batch_jobs(jobs)
    
    # 결과 요약
    print("\n📊 배치 결과 요약:")
    for r in results:
        if r['status'] == 'success':
            radar = r['result']['report']['radar_chart']
            print(f"\n✅ {r['job_id']}")
            print(f"   평균 점수: {radar['average']:.1f}/100")
        else:
            print(f"\n❌ {r['job_id']}")
            print(f"   에러: {r['error']}")


def main():
    print("\n" + "="*70)
    print("🎤 보컬 분석 워커 테스트")
    print("="*70)
    print("\n테스트 모드 선택:")
    print("  1. 단일 작업 테스트")
    print("  2. 배치 작업 테스트")
    print("  3. 둘 다 실행")
    
    choice = input("\n선택 (1/2/3): ").strip()
    
    if choice == "1":
        test_single()
    elif choice == "2":
        test_batch()
    elif choice == "3":
        test_single()
        print("\n" + "="*70 + "\n")
        test_batch()
    else:
        print("❌ 잘못된 선택입니다")
        return
    
    print("\n" + "="*70)
    print("✅ 테스트 완료!")
    print("="*70)


if __name__ == "__main__":
    main()


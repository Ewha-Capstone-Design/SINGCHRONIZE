"""
추천 시스템 실행 스크립트

곡 특징 추출 + 점수 계산을 한 번에 실행
"""
import sys
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="추천 시스템 실행 (곡 특징 추출 + 점수 계산)"
    )
    parser.add_argument(
        "--songs_dir",
        type=str,
        default="data/songs_raw",
        help="곡 파일들이 있는 디렉토리 (기본값: data/songs_raw)"
    )
    parser.add_argument(
        "--user_file",
        type=str,
        default="vocal_analysis/test_output/test1_result.json",
        help="유저 특징 파일 경로 (기본값: vocal_analysis/test_output/test1_result.json)"
    )
    parser.add_argument(
        "--out_features",
        type=str,
        default="artifacts/song_features",
        help="곡 특징 저장 디렉토리 (기본값: artifacts/song_features)"
    )
    parser.add_argument(
        "--out_results",
        type=str,
        default="results",
        help="결과 저장 디렉토리 (기본값: results)"
    )
    parser.add_argument(
        "--no-vocal-separation",
        action="store_true",
        help="보컬 분리 스킵 (디버그용)"
    )
    parser.add_argument(
        "--skip-features",
        action="store_true",
        help="곡 특징 추출 스킵 (이미 추출된 경우)"
    )
    parser.add_argument(
        "--skip-scoring",
        action="store_true",
        help="점수 계산 스킵 (특징 추출만 실행)"
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("🎵 추천 시스템 실행")
    print("="*70)
    
    # 1. 곡 파일 확인
    songs_dir = Path(args.songs_dir)
    if not songs_dir.exists():
        print(f"\n❌ 곡 디렉토리가 없습니다: {songs_dir}")
        print(f"\n📁 곡 파일 준비 방법:")
        print(f"   1. {songs_dir} 디렉토리를 생성하세요")
        print(f"   2. 곡 파일들을 {songs_dir}에 복사하세요")
        print(f"      지원 포맷: .mp3, .wav, .m4a, .flac, .mp4")
        print(f"      예: {songs_dir}/song1.mp3, {songs_dir}/song2.mp3, ...")
        sys.exit(1)
    
    # 곡 파일 찾기
    audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.mp4']
    song_files = []
    for ext in audio_extensions:
        song_files.extend(list(songs_dir.glob(f"*{ext}")))
    
    if not song_files:
        print(f"\n❌ 곡 파일을 찾을 수 없습니다: {songs_dir}")
        print(f"   지원 포맷: {', '.join(audio_extensions)}")
        sys.exit(1)
    
    print(f"\n📁 곡 파일: {len(song_files)}개 발견")
    for i, song_file in enumerate(song_files[:5], 1):
        print(f"   {i}. {song_file.name}")
    if len(song_files) > 5:
        print(f"   ... 외 {len(song_files) - 5}개")
    
    # 2. 유저 파일 확인
    user_file = Path(args.user_file)
    if not user_file.exists():
        print(f"\n❌ 유저 특징 파일이 없습니다: {user_file}")
        print(f"   기본 경로: vocal_analysis/test_output/test1_result.json")
        sys.exit(1)
    
    print(f"\n👤 유저 특징: {user_file}")
    
    # 3. 곡 특징 추출
    if not args.skip_features:
        print("\n" + "="*70)
        print("🎵 Step 1: 곡 특징 추출")
        print("="*70)
        
        from song_feature_worker import process_songs_batch
        
        try:
            results = process_songs_batch(
                songs_dir=str(songs_dir),
                output_dir=args.out_features,
                use_vocal_separation=not args.no_vocal_separation
            )
            
            success_count = sum(1 for r in results if r['status'] == 'success')
            if success_count == 0:
                print("\n❌ 모든 곡 특징 추출 실패")
                sys.exit(1)
            
            print(f"\n✅ 곡 특징 추출 완료: {success_count}/{len(song_files)}개 성공")
            
        except Exception as e:
            print(f"\n❌ 곡 특징 추출 실패: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("\n⏭️  곡 특징 추출 스킵 (--skip-features)")
    
    # 4. 점수 계산
    if not args.skip_scoring:
        print("\n" + "="*70)
        print("🎯 Step 2: 점수 계산 및 랭킹")
        print("="*70)
        
        from scoring_runner import run_scoring
        
        try:
            results = run_scoring(
                user_features_path=str(user_file),
                song_features_dir=args.out_features,
                output_dir=args.out_results
            )
            
            print(f"\n✅ 점수 계산 완료!")
            print(f"   결과: {args.out_results}/scores.csv")
            print(f"   랭킹: {args.out_results}/ranked.json")
            
        except Exception as e:
            print(f"\n❌ 점수 계산 실패: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("\n⏭️  점수 계산 스킵 (--skip-scoring)")
    
    print("\n" + "="*70)
    print("✅ 전체 프로세스 완료!")
    print("="*70)
    print(f"\n📊 결과 확인:")
    print(f"   CSV: {args.out_results}/scores.csv")
    print(f"   JSON: {args.out_results}/ranked.json")


if __name__ == "__main__":
    main()


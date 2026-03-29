"""
1차 추천 워커

기본 흐름 (프로덕션):
1. user_vocal_profiles 에서 유저 스코어링 특징 로드
   (보컬 분석 워커가 UserVocalPipeline 1회 실행 후 DB에 넣은 값)
2. song_features 조회
3. scoring_runner.score_song 으로 랭킹

폴백 (로컬/비상만):
  환경변수 FIRST_REC_FORCE_PIPELINE=1 일 때만 S3 다운로드 + UserVocalPipeline 재실행.
"""
import json
import os
import tempfile
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# 환경 변수 로드
env_paths = [
    Path(__file__).parent.parent.parent / ".env",  # ai/.env
    Path(__file__).parent.parent.parent.parent / ".env",  # 프로젝트 루트/.env
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ .env 파일 로드: {env_path}")
        break
else:
    load_dotenv()
    print("⚠️  .env 파일을 찾지 못했습니다. 기본 위치에서 시도합니다.")

# Supabase 클라이언트
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
USER_VOCAL_PROFILES_TABLE = (os.getenv("USER_VOCAL_PROFILES_TABLE") or "user_vocal_profiles").strip()

# vocal_analysis 모듈 import
import sys
vocal_analysis_path = Path(__file__).parent.parent / "vocal_analysis"
sys.path.insert(0, str(vocal_analysis_path.parent))
from vocal_analysis.user_song_aligned_features import try_user_features_from_db_profile_row

# scoring_runner 모듈 import
scoring_runner_path = Path(__file__).parent.parent
sys.path.insert(0, str(scoring_runner_path))
from scoring_runner import score_song


def get_supabase_client():
    """Supabase 클라이언트 생성"""
    if not SUPABASE_URL:
        raise RuntimeError(
            "SUPABASE_URL이 .env에 설정되지 않았습니다.\n"
            ".env 파일에 다음을 추가하세요:\n"
            "SUPABASE_URL=https://your-project.supabase.co"
        )
    
    if not SUPABASE_KEY:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY가 .env에 설정되지 않았습니다.\n"
            ".env 파일에 다음을 추가하세요:\n"
            "SUPABASE_SERVICE_ROLE_KEY=your-service-role-key"
        )
    
    from supabase import create_client, Client
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"✓ Supabase 클라이언트 생성 성공")
        return client
    except Exception as e:
        raise RuntimeError(f"Supabase 클라이언트 생성 실패: {e}") from e


def s3_download(bucket: str, key: str, local_path: Path) -> None:
    """S3에서 파일 다운로드"""
    s3 = boto3.client("s3")
    print(f"  - S3 다운로드: s3://{bucket}/{key} -> {local_path}")
    s3.download_file(bucket, key, str(local_path))


def get_all_song_features_from_db() -> List[Dict]:
    """
    DB에서 모든 song_features 조회
    
    Returns:
        song_features_list: 곡 특징 리스트
    """
    supabase = get_supabase_client()
    
    print("\n[DB 조회] song_features 테이블에서 모든 곡 특징 조회 중...")
    song_features_list = []
    start = 0
    step = 1000
    
    while True:
        res = (
            supabase.table("song_features")
            .select("*")
            .range(start, start + step - 1)
            .execute()
        )
        
        batch = res.data or []
        if not batch:
            break
        
        # vector 타입을 numpy array로 변환
        for row in batch:
            # song_repr_embedding이 문자열로 오는 경우 처리
            embedding = row.get('song_repr_embedding')
            if isinstance(embedding, str):
                # '[1,2,3]' 형식의 문자열을 파싱
                embedding = embedding.strip('[]').split(',')
                embedding = [float(x.strip()) for x in embedding]
            elif isinstance(embedding, list):
                embedding = [float(x) for x in embedding]
            else:
                # 이미 numpy array일 수도 있음
                embedding = list(embedding) if hasattr(embedding, '__iter__') else []
            
            # song_features 형식으로 변환 (scoring_runner.py의 score_song 함수가 기대하는 형식)
            song_feature = {
                'song_id': row['song_id'],
                'song_repr_embedding': embedding,
                'f0_p5': row.get('f0_p5', 0.0),
                'f0_p25': row.get('f0_p25', 0.0),
                'f0_p75': row.get('f0_p75', 0.0),
                'f0_p95': row.get('f0_p95', 0.0),
                'voiced_ratio': row.get('voiced_ratio', 0.0),
                'timbre': {
                    'brightness': row.get('timbre_brightness', 0.0),
                    'roughness': row.get('timbre_roughness', 0.0),
                    'body': row.get('timbre_body', 0.0),
                    'clarity': row.get('timbre_clarity', 0.0),
                    'warmth': row.get('timbre_warmth', 0.0),
                    'f0_mean': row.get('timbre_f0_mean', 0.0),
                    'formant_f1': row.get('timbre_formant_f1', 0.0),
                    'formant_f2': row.get('timbre_formant_f2', 0.0),
                    'spectral_centroid': row.get('timbre_spectral_centroid', 0.0)
                }
            }
            song_features_list.append(song_feature)
        
        if len(batch) < step:
            break
        start += step
    
    print(f"✓ 총 {len(song_features_list)}개 곡 특징 조회 완료")
    return song_features_list


def extract_user_features_from_audio(audio_path: str, output_dir: Optional[str] = None) -> Dict:
    """
    유저 오디오에서 특징 추출
    
    Args:
        audio_path: 유저 오디오 파일 경로
        output_dir: 출력 디렉토리 (None이면 임시 디렉토리 사용)
    
    Returns:
        user_features: 유저 특징 딕셔너리 (scoring_runner.py의 score_song 함수가 기대하는 형식)
    """
    print("\n[유저 특징 추출] UserVocalPipeline 실행 중...")
    
    # 출력 디렉토리 설정
    if output_dir is None:
        output_dir = Path(audio_path).parent / "user_features_temp"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # FIRST_REC_FORCE_PIPELINE=1 폴백 경로에서만 필요하므로 지연 import
    from vocal_analysis.user_vocal_pipeline import UserVocalPipeline

    # UserVocalPipeline 실행
    pipeline = UserVocalPipeline()
    result = pipeline.process(
        audio_path=audio_path,
        output_dir=str(output_path),
        save_features=True
    )
    
    # scoring_runner.py의 score_song 함수가 기대하는 형식으로 변환
    embedding_data = result['embedding']
    
    # pitch_profile에서 퍼센타일 정보 추출
    pitch_profile = embedding_data.get('pitch_profile', {})
    
    # f0_min/max에서 퍼센타일 근사 (scoring_runner.py의 로직 참고)
    f0_min = pitch_profile.get('f0_min', 0.0)
    f0_max = pitch_profile.get('f0_max', 0.0)
    tessitura_low = pitch_profile.get('tessitura_low', f0_min)
    tessitura_high = pitch_profile.get('tessitura_high', f0_max)
    
    # features에서 f0_contour가 있으면 퍼센타일 계산
    if 'features' in result and 'pitch' in result['features']:
        pitch_data = result['features']['pitch']
        f0_contour = np.array(pitch_data.get('f0_contour', []))
        voiced_mask = np.array(pitch_data.get('voiced_mask', f0_contour > 0))
        f0_voiced = f0_contour[(f0_contour > 0) & voiced_mask]
        
        if len(f0_voiced) > 0:
            pitch_profile_with_percentiles = {
                'f0_p2': float(np.percentile(f0_voiced, 2)),
                'f0_p98': float(np.percentile(f0_voiced, 98)),
                'f0_p25': float(np.percentile(f0_voiced, 25)),
                'f0_p75': float(np.percentile(f0_voiced, 75)),
                'f0_p5': float(np.percentile(f0_voiced, 5)),
                'f0_p95': float(np.percentile(f0_voiced, 95)),
                'f0_min': f0_min,
                'f0_max': f0_max,
                'tessitura_low': tessitura_low,
                'tessitura_high': tessitura_high
            }
        else:
            # f0_voiced가 없으면 f0_min/max로 근사
            pitch_profile_with_percentiles = {
                'f0_p2': f0_min * 0.95 if f0_min > 0 else 0.0,
                'f0_p98': f0_max * 1.01 if f0_max > 0 else 0.0,
                'f0_p25': tessitura_low,
                'f0_p75': tessitura_high,
                'f0_p5': f0_min * 0.9 if f0_min > 0 else 0.0,
                'f0_p95': f0_max * 0.98 if f0_max > 0 else 0.0,
                'f0_min': f0_min,
                'f0_max': f0_max,
                'tessitura_low': tessitura_low,
                'tessitura_high': tessitura_high
            }
    else:
        # features가 없으면 f0_min/max로 근사
        pitch_profile_with_percentiles = {
            'f0_p2': f0_min * 0.95 if f0_min > 0 else 0.0,
            'f0_p98': f0_max * 1.01 if f0_max > 0 else 0.0,
            'f0_p25': tessitura_low,
            'f0_p75': tessitura_high,
            'f0_p5': f0_min * 0.9 if f0_min > 0 else 0.0,
            'f0_p95': f0_max * 0.98 if f0_max > 0 else 0.0,
            'f0_min': f0_min,
            'f0_max': f0_max,
            'tessitura_low': tessitura_low,
            'tessitura_high': tessitura_high
        }
    
    # voiced_ratio 계산
    voiced_ratio = 0.0
    if 'features' in result and 'pitch' in result['features']:
        pitch_data = result['features']['pitch']
        if 'voiced_mask' in pitch_data:
            voiced_mask = np.array(pitch_data['voiced_mask'])
            voiced_ratio = float(np.sum(voiced_mask) / len(voiced_mask)) if len(voiced_mask) > 0 else 0.0
    
    # user_features 구성
    user_features = {
        'representative_embedding': embedding_data['representative_embedding'],
        'pitch_profile': pitch_profile_with_percentiles,
        'timbre_vector': embedding_data['timbre_vector'],
        'voiced_ratio': voiced_ratio
    }
    
    # features도 포함 (scoring_runner.py에서 사용할 수 있도록)
    if 'features' in result:
        user_features['features'] = result['features']
    
    print(f"✓ 유저 특징 추출 완료")
    print(f"  - 임베딩 차원: {len(user_features['representative_embedding'])}")
    print(f"  - 음역대: {pitch_profile_with_percentiles.get('f0_p2', 0):.1f}Hz ~ {pitch_profile_with_percentiles.get('f0_p98', 0):.1f}Hz")
    
    return user_features


def try_load_user_features_from_vocal_profile(user_id: str):
    """
    user_vocal_profiles 에 song_features 정렬 스코어링 컬럼이 있으면
    파이프라인 없이 score_song용 user_features 반환.
    """
    supabase = get_supabase_client()
    res = (
        supabase.table(USER_VOCAL_PROFILES_TABLE)
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        return None
    return try_user_features_from_db_profile_row(rows[0])


def process_first_recommendation(
    job_id: str,
    user_id: str,
    s3_key: str,
    output_dir: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict:
    """
    1차 추천 처리 메인 함수
    
    Args:
        job_id: 작업 ID
        user_id: 유저 ID
        s3_key: 유저 녹음 S3 키
        output_dir: 출력 디렉토리 (None이면 임시 디렉토리 사용)
        limit: 처리할 최대 곡 개수 (None이면 모두)
    
    Returns:
        result: {
            'status': 'success' or 'failed',
            'job_id': job_id,
            'user_id': user_id,
            'ranked_results': 정렬된 점수 결과 리스트,
            'error': 에러 메시지 (실패 시)
        }
    """
    print("\n" + "="*70)
    print(f"🎯 1차 추천 처리 시작")
    print("="*70)
    print(f"  - job_id: {job_id}")
    print(f"  - user_id: {user_id}")
    print(f"  - s3_key: {s3_key}")
    print("="*70)
    
    # 임시 디렉토리 생성
    if output_dir is None:
        temp_dir = Path(tempfile.mkdtemp(prefix=f"first_recommendation_{job_id}_"))
    else:
        temp_dir = Path(output_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        force_pipeline = os.getenv("FIRST_REC_FORCE_PIPELINE", "").lower() in (
            "1",
            "true",
            "yes",
        )

        if force_pipeline:
            print(
                "\n[Step 1-2] FIRST_REC_FORCE_PIPELINE: S3 + UserVocalPipeline "
                "(DB 프로필을 쓰지 않음)"
            )
            if not S3_BUCKET:
                raise RuntimeError("파이프라인 폴백 시 S3_BUCKET_NAME이 .env에 필요합니다.")

            local_audio_path = temp_dir / f"{job_id}_user_audio.m4a"
            s3_download(S3_BUCKET, s3_key, local_audio_path)
            print(f"✓ 다운로드 완료: {local_audio_path}")

            print("\n[Step 2] 유저 특징 추출 (UserVocalPipeline)")
            user_features = extract_user_features_from_audio(
                audio_path=str(local_audio_path),
                output_dir=str(temp_dir / "user_features"),
            )
        else:
            print(
                "\n[Step 1-2] user_vocal_profiles 에서 유저 스코어링 특징 로드 "
                "(보컬 분석 완료 후 저장된 값 — UserVocalPipeline 미실행)"
            )
            user_features = try_load_user_features_from_vocal_profile(user_id)
            if user_features is None:
                raise RuntimeError(
                    "1차 추천: user_vocal_profiles 에 1차 추천용 컬럼(vocal_repr_embedding, "
                    "f0_*, timbre_* 등)이 채워져 있지 않습니다.\n"
                    "먼저 보컬 분석 워커(SQS)로 분석을 완료했는지, "
                    "마이그레이션(sql/add_user_vocal_profiles_song_aligned_columns.sql)을 적용했는지 확인하세요.\n"
                    "로컬에서만 파이프라인으로 돌리려면 FIRST_REC_FORCE_PIPELINE=1"
                )
        
        # Step 3: DB에서 song_features 조회
        print("\n[Step 3] DB에서 song_features 조회")
        song_features_list = get_all_song_features_from_db()
        
        if not song_features_list:
            raise RuntimeError("DB에 song_features가 없습니다.")
        
        # limit 적용
        if limit:
            song_features_list = song_features_list[:limit]
            print(f"  - limit 적용: {limit}개 곡만 처리")
        
        # Step 4: 점수 계산
        print(f"\n[Step 4] 점수 계산 ({len(song_features_list)}개 곡)")
        results = []
        for i, song_features in enumerate(song_features_list, 1):
            song_id = song_features['song_id']
            print(f"  [{i}/{len(song_features_list)}] {song_id}...", end=" ")
            
            try:
                score_result = score_song(user_features, song_features)
                results.append(score_result)
                print(f"✓ (final_score: {score_result['final_score']:.4f})")
            except Exception as e:
                print(f"❌ {e}")
                results.append({
                    'song_id': song_id,
                    'final_score': 0.0,
                    'error': str(e)
                })
        
        # Step 5: 정렬
        print("\n[Step 5] 결과 정렬")
        results_sorted = sorted(results, key=lambda x: x['final_score'], reverse=True)
        
        # Step 6: 결과 저장 (선택적)
        print("\n[Step 6] 결과 저장")
        output_file = temp_dir / "ranked_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_sorted, f, indent=2, ensure_ascii=False)
        print(f"✓ 결과 저장: {output_file}")
        
        # 요약 출력
        print("\n" + "="*70)
        print("📊 랭킹 결과 (상위 10개)")
        print("="*70)
        for i, result in enumerate(results_sorted[:10], 1):
            print(f"{i}. {result['song_id']}: {result['final_score']:.4f}")
            if 'ecapa_score' in result:
                print(f"   ECAPA: {result.get('ecapa_score', 0):.4f}, "
                      f"Pitch: {result.get('pitch_total', result.get('pitch_score', 0)):.4f}, "
                      f"Timbre: {result.get('timbre_score', 0):.4f}")
        print("="*70 + "\n")
        
        return {
            'status': 'success',
            'job_id': job_id,
            'user_id': user_id,
            'ranked_results': results_sorted,
            'output_file': str(output_file),
            'total_songs': len(song_features_list),
            'processed_songs': len(results)
        }
        
    except Exception as e:
        print(f"\n❌ 1차 추천 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'status': 'failed',
            'job_id': job_id,
            'user_id': user_id,
            'error': str(e)
        }


# CLI 실행
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="1차 추천 워커"
    )
    parser.add_argument(
        "--job-id",
        type=str,
        required=True,
        help="작업 ID"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        required=True,
        help="유저 ID"
    )
    parser.add_argument(
        "--s3-key",
        type=str,
        required=True,
        help="유저 녹음 S3 키"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="출력 디렉토리 (기본값: 임시 디렉토리)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="처리할 최대 곡 개수 (기본값: 모두)"
    )
    
    args = parser.parse_args()
    
    try:
        result = process_first_recommendation(
            job_id=args.job_id,
            user_id=args.user_id,
            s3_key=args.s3_key,
            output_dir=args.output_dir,
            limit=args.limit
        )
        
        if result['status'] == 'success':
            print("\n✅ 1차 추천 처리 완료!")
            print(f"   결과 파일: {result.get('output_file', 'N/A')}")
            print(f"   처리된 곡: {result.get('processed_songs', 0)}개")
            exit(0)
        else:
            print(f"\n❌ 1차 추천 처리 실패: {result.get('error', 'Unknown error')}")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)






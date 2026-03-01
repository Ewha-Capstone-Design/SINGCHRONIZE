"""
음원 분석 워커

S3에서 음원을 다운로드하여:
1. 보컬 분리 (Demucs)
2. 보컬 분석 (UserVocalPipeline)
3. 벡터 추출 및 S3 업로드

테스트용으로 한 두 곡 처리 가능
"""
import os
import json
import tempfile
from pathlib import Path
from typing import Dict, Optional, List
import warnings
warnings.filterwarnings('ignore')

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from supabase import create_client, Client

# vocal_analysis 모듈 import
import sys
vocal_analysis_path = Path(__file__).parent / "vocal_analysis"
sys.path.insert(0, str(vocal_analysis_path.parent))
from vocal_analysis.audio_preprocessing import remove_mr
from vocal_analysis.user_vocal_pipeline import UserVocalPipeline

# 환경 변수 로드
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
S3_VECTOR_PREFIX = os.getenv("S3_VECTOR_PREFIX", "vectors/songs").strip().strip("/")


def get_supabase_client() -> Client:
    """Supabase 클라이언트 생성"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY가 .env에 필요합니다.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def s3_download(bucket: str, key: str, local_path: Path) -> None:
    """S3에서 파일 다운로드"""
    s3 = boto3.client("s3")
    print(f"  - S3 다운로드: s3://{bucket}/{key} -> {local_path}")
    s3.download_file(bucket, key, str(local_path))


def s3_upload(local_path: Path, bucket: str, key: str) -> None:
    """S3에 파일 업로드"""
    s3 = boto3.client("s3")
    print(f"  - S3 업로드: {local_path} -> s3://{bucket}/{key}")
    s3.upload_file(str(local_path), bucket, key)


def upload_vector_to_s3(
    embedding_data: Dict,
    song_id: str,
    bucket: str,
    prefix: str = S3_VECTOR_PREFIX
) -> str:
    """
    벡터 데이터를 JSON으로 변환하여 S3에 업로드
    
    Args:
        embedding_data: embedding 딕셔너리 (representative_embedding, pitch_profile, timbre_vector 등)
        song_id: 곡 ID
        bucket: S3 버킷 이름
        prefix: S3 키 prefix
    
    Returns:
        s3_key: 업로드된 S3 키
    """
    # 임시 파일에 JSON 저장
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(embedding_data, f, indent=2, ensure_ascii=False)
        temp_file = Path(f.name)
    
    try:
        # S3 키 생성
        s3_key = f"{prefix}/{song_id}_vector.json"
        
        # S3 업로드
        s3_upload(temp_file, bucket, s3_key)
        
        return s3_key
    finally:
        # 임시 파일 삭제
        temp_file.unlink(missing_ok=True)


class SongAnalysisWorker:
    """
    음원 분석 워커
    
    S3에서 음원을 다운로드하여 보컬 분석 후 벡터를 S3에 업로드
    """
    
    def __init__(
        self,
        s3_bucket: Optional[str] = None,
        s3_vector_prefix: Optional[str] = None
    ):
        """
        Args:
            s3_bucket: S3 버킷 이름 (None이면 환경 변수 사용)
            s3_vector_prefix: 벡터 저장 S3 prefix (None이면 환경 변수 사용)
        """
        self.s3_bucket = s3_bucket or S3_BUCKET
        self.s3_vector_prefix = s3_vector_prefix or S3_VECTOR_PREFIX
        
        if not self.s3_bucket:
            raise RuntimeError("S3_BUCKET_NAME이 .env에 필요합니다.")
        
        # 보컬 분석 파이프라인 초기화
        self.pipeline = UserVocalPipeline()
        
        print("🎵 음원 분석 워커 초기화 완료")
        print(f"  - S3 Bucket: {self.s3_bucket}")
        print(f"  - Vector Prefix: {self.s3_vector_prefix}")
    
    def process_song(
        self,
        song_id: str,
        raw_s3_key: str,
        output_dir: Optional[str] = None
    ) -> Dict:
        """
        단일 곡 처리
        
        Args:
            song_id: 곡 ID
            raw_s3_key: S3에 저장된 원본 음원 키
            output_dir: 임시 파일 저장 디렉토리 (None이면 임시 디렉토리 사용)
        
        Returns:
            result: {
                'status': 'success' or 'failed',
                'song_id': song_id,
                'vector_s3_key': 벡터 S3 키,
                'result': 분석 결과 (성공 시),
                'error': 에러 메시지 (실패 시)
            }
        """
        print("\n" + "="*70)
        print(f"🎵 곡 분석 시작: song_id={song_id}")
        print("="*70)
        
        # 임시 디렉토리 생성
        if output_dir is None:
            temp_dir = Path(tempfile.mkdtemp(prefix=f"song_analysis_{song_id}_"))
        else:
            temp_dir = Path(output_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Step 1: S3에서 음원 다운로드
            print("\n[Step 1] S3에서 음원 다운로드")
            local_audio_path = temp_dir / f"{song_id}_raw.mp4"
            s3_download(self.s3_bucket, raw_s3_key, local_audio_path)
            print(f"✓ 다운로드 완료: {local_audio_path}")
            
            # Step 2: 보컬 분리
            print("\n[Step 2] 보컬 분리 (Demucs)")
            vocals_path = remove_mr(
                audio_path=str(local_audio_path),
                output_dir=str(temp_dir / "vocals")
            )
            print(f"✓ 보컬 분리 완료: {vocals_path}")
            
            # Step 3: 보컬 분석
            print("\n[Step 3] 보컬 분석")
            analysis_result = self.pipeline.process(
                audio_path=vocals_path,
                output_dir=str(temp_dir / "analysis"),
                save_features=False  # 메타데이터만 저장
            )
            print("✓ 보컬 분석 완료")
            
            # Step 4: 벡터 추출 및 S3 업로드
            print("\n[Step 4] 벡터 S3 업로드")
            embedding_data = analysis_result['embedding']
            vector_s3_key = upload_vector_to_s3(
                embedding_data=embedding_data,
                song_id=song_id,
                bucket=self.s3_bucket,
                prefix=self.s3_vector_prefix
            )
            print(f"✓ 벡터 업로드 완료: s3://{self.s3_bucket}/{vector_s3_key}")
            
            print("\n" + "="*70)
            print(f"✅ 곡 분석 완료: song_id={song_id}")
            print("="*70)
            
            return {
                'status': 'success',
                'song_id': song_id,
                'vector_s3_key': vector_s3_key,
                'result': analysis_result
            }
            
        except Exception as e:
            print(f"\n❌ 곡 분석 실패: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'status': 'failed',
                'song_id': song_id,
                'error': str(e)
            }
        
        finally:
            # 임시 파일 정리 (선택적 - 디버깅 시 남겨둘 수 있음)
            # temp_dir의 파일들을 삭제하려면 여기서 처리
            pass
    
    def process_songs_from_db(
        self,
        song_ids: List[str],
        supabase: Optional[Client] = None
    ) -> List[Dict]:
        """
        DB에서 곡 정보를 가져와서 처리
        
        Args:
            song_ids: 곡 ID 리스트
            supabase: Supabase 클라이언트 (None이면 자동 생성)
        
        Returns:
            results: 처리 결과 리스트
        """
        if supabase is None:
            supabase = get_supabase_client()
        
        # DB에서 곡 정보 조회
        print(f"\n📋 DB에서 {len(song_ids)}개 곡 정보 조회")
        res = (
            supabase.table("songs")
            .select("id, title, artist, raw_s3_key")
            .in_("id", song_ids)
            .execute()
        )
        
        songs = res.data or []
        if len(songs) != len(song_ids):
            found_ids = {s['id'] for s in songs}
            missing_ids = set(song_ids) - found_ids
            print(f"⚠️  일부 곡을 찾을 수 없습니다: {missing_ids}")
        
        results = []
        for i, song in enumerate(songs, 1):
            song_id = song['id']
            title = song.get('title', 'Unknown')
            artist = song.get('artist', 'Unknown')
            raw_s3_key = song.get('raw_s3_key')
            
            if not raw_s3_key:
                print(f"\n[SKIP] {i}/{len(songs)} {title} - {artist} (raw_s3_key 없음)")
                results.append({
                    'status': 'failed',
                    'song_id': song_id,
                    'error': 'raw_s3_key가 없습니다'
                })
                continue
            
            print(f"\n{'='*70}")
            print(f"[{i}/{len(songs)}] {title} - {artist}")
            print(f"{'='*70}")
            
            result = self.process_song(
                song_id=song_id,
                raw_s3_key=raw_s3_key
            )
            results.append(result)
        
        # 배치 요약
        print("\n" + "="*70)
        print("📊 배치 처리 완료")
        print("="*70)
        success_count = sum(1 for r in results if r['status'] == 'success')
        print(f"✅ 성공: {success_count}/{len(songs)}")
        print(f"❌ 실패: {len(songs) - success_count}/{len(songs)}")
        print("="*70 + "\n")
        
        return results


# ============================================================================
# 테스트용 헬퍼 함수
# ============================================================================

def test_single_song(song_id: str, raw_s3_key: str):
    """
    단일 곡 테스트
    
    Args:
        song_id: 곡 ID
        raw_s3_key: S3에 저장된 원본 음원 키
    """
    worker = SongAnalysisWorker()
    result = worker.process_song(song_id, raw_s3_key)
    return result


def test_songs_from_db(song_ids: List[str]):
    """
    DB에서 곡 정보를 가져와서 테스트
    
    Args:
        song_ids: 곡 ID 리스트
    """
    worker = SongAnalysisWorker()
    results = worker.process_songs_from_db(song_ids)
    return results


# ============================================================================
# CLI 실행
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="음원 분석 워커 (보컬 분리 + 분석 + 벡터 업로드)"
    )
    parser.add_argument(
        "--song-ids",
        type=str,
        nargs="+",
        required=True,
        help="처리할 곡 ID 리스트 (예: --song-ids song1 song2)"
    )
    parser.add_argument(
        "--raw-s3-key",
        type=str,
        help="직접 S3 키 지정 (song-ids와 함께 사용 불가)"
    )
    
    args = parser.parse_args()
    
    # 필수 체크
    if not S3_BUCKET:
        print("❌ S3_BUCKET_NAME이 .env에 필요합니다.")
        exit(1)
    
    worker = SongAnalysisWorker()
    
    try:
        if args.raw_s3_key:
            # 직접 S3 키 지정 모드
            if len(args.song_ids) != 1:
                print("❌ --raw-s3-key 사용 시 song-id는 1개만 가능합니다.")
                exit(1)
            
            result = worker.process_song(
                song_id=args.song_ids[0],
                raw_s3_key=args.raw_s3_key
            )
            
            if result['status'] == 'success':
                print(f"\n✅ 처리 완료!")
                print(f"📦 벡터 S3 키: {result['vector_s3_key']}")
                exit(0)
            else:
                print(f"\n❌ 처리 실패: {result['error']}")
                exit(1)
        else:
            # DB에서 조회 모드
            results = worker.process_songs_from_db(args.song_ids)
            
            success_count = sum(1 for r in results if r['status'] == 'success')
            if success_count == len(results):
                print("\n✅ 모든 곡 처리 완료!")
                exit(0)
            else:
                print(f"\n⚠️  일부 곡 처리 실패: {success_count}/{len(results)} 성공")
                exit(1)
    
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


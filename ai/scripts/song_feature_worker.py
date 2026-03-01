"""
노래 분석 워커

곡 원본에서 보컬 분리 후 특징 추출하여 저장
- ECAPA 임베딩
- 음역대 (F0 퍼센타일)
- 음색 프로파일

S3에서 곡을 다운로드하고 DB에 저장하는 기능 포함
"""
import json
import os
import tempfile
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List
import warnings
warnings.filterwarnings('ignore')

import librosa
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

# 환경 변수 로드 (.env 파일 위치: ai 디렉토리 또는 프로젝트 루트)
env_paths = [
    Path(__file__).parent.parent / ".env",  # ai/.env
    Path(__file__).parent.parent.parent / ".env",  # 프로젝트 루트/.env
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ .env 파일 로드: {env_path}")
        break
else:
    # .env 파일을 찾지 못했어도 기본 load_dotenv() 시도
    load_dotenv()
    print("⚠️  .env 파일을 찾지 못했습니다. 기본 위치에서 시도합니다.")

# vocal_analysis 모듈 import
import sys
vocal_analysis_path = Path(__file__).parent / "vocal_analysis"
sys.path.insert(0, str(vocal_analysis_path.parent))
from vocal_analysis.audio_preprocessing import AudioPreprocessor, remove_mr
from vocal_analysis.feature_extraction import FeatureExtractor

# 환경 변수
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
# Connection Pooler 사용 여부 (포트 6543)
USE_CONNECTION_POOLER = os.getenv("USE_CONNECTION_POOLER", "false").lower() == "true"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


# ============================================================================
# S3 및 DB 유틸리티 함수
# ============================================================================

def s3_download(bucket: str, key: str, local_path: Path) -> None:
    """S3에서 파일 다운로드"""
    s3 = boto3.client("s3")
    print(f"  - S3 다운로드: s3://{bucket}/{key} -> {local_path}")
    s3.download_file(bucket, key, str(local_path))


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
            "SUPABASE_SERVICE_ROLE_KEY=your-service-role-key\n"
            "\n참고: SECRET_KEY가 아니라 SUPABASE_SERVICE_ROLE_KEY를 사용하세요."
        )
    
    # 디버깅: 키 정보 출력
    print(f"\n📋 Supabase 연결 정보:")
    print(f"  - SUPABASE_URL: {SUPABASE_URL}")
    print(f"  - SUPABASE_SERVICE_ROLE_KEY 길이: {len(SUPABASE_KEY)} 문자")
    print(f"  - KEY 시작: {SUPABASE_KEY[:40]}...")
    print(f"  - KEY 형식: {'sb_secret_ (새 형식)' if SUPABASE_KEY.startswith('sb_secret_') else 'eyJ (JWT 형식)' if SUPABASE_KEY.startswith('eyJ') else '알 수 없음'}")
    
    # 키 길이 검증 (sb_secret_ 형식은 보통 더 길어야 함)
    if SUPABASE_KEY.startswith('sb_secret_') and len(SUPABASE_KEY) < 100:
        print(f"\n⚠️  경고: sb_secret_ 키가 너무 짧습니다 ({len(SUPABASE_KEY)}자).")
        print("   Supabase 대시보드에서 눈 아이콘을 클릭해 전체 키를 복사했는지 확인하세요.")
    
    from supabase import create_client, Client
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"✓ Supabase 클라이언트 생성 성공")
        return client
    except Exception as e:
        error_msg = str(e)
        raise RuntimeError(
            f"\n❌ Supabase 클라이언트 생성 실패\n"
            f"에러: {error_msg}\n"
            f"\n현재 설정:\n"
            f"  - SUPABASE_URL: {SUPABASE_URL}\n"
            f"  - SUPABASE_SERVICE_ROLE_KEY 길이: {len(SUPABASE_KEY)} 문자\n"
            f"  - KEY 시작: {SUPABASE_KEY[:40]}...\n"
            f"\n확인 사항:\n"
            f"1. .env 파일에 'SUPABASE_SERVICE_ROLE_KEY' (SECRET_KEY 아님)가 있는지 확인\n"
            f"2. Supabase 대시보드 → Settings → API → Secret keys에서 'service_role' 'secret' 키 전체를 복사\n"
            f"3. sb_secret_ 형식이라면 눈 아이콘을 클릭해 전체 키를 복사했는지 확인\n"
            f"4. 키에 공백이나 따옴표가 포함되지 않았는지 확인"
        ) from e

def get_song_from_db(song_id: str) -> Optional[Dict]:
    """
    DB에서 곡 정보 조회 (Supabase 클라이언트 사용)
    
    Args:
        song_id: 곡 ID (UUID)
    
    Returns:
        song: {id, title, artist, raw_s3_key} 또는 None
    """
    supabase = get_supabase_client()
    
    res = (
        supabase.table("songs")
        .select("id, title, artist, raw_s3_key")
        .eq("id", song_id)
        .execute()
    )
    
    if res.data and len(res.data) > 0:
        return res.data[0]
    return None


def get_unprocessed_song_ids(limit: Optional[int] = None) -> List[str]:
    """
    처리되지 않은 곡 ID 목록 가져오기 (song_features 테이블에 없는 곡)
    
    Args:
        limit: 가져올 최대 개수 (None이면 모두)
    
    Returns:
        song_ids: 처리되지 않은 곡 ID 리스트
    """
    supabase = get_supabase_client()
    
    # 1. song_features 테이블에 있는 모든 song_id 가져오기 (tj_to_db.py처럼 supabase 클라이언트 사용)
    print("\n[Step 1] 이미 처리된 곡 ID 조회 중...")
    processed_ids = set()
    
    try:
        # tj_to_db.py처럼 supabase.table().select().execute() 패턴 사용
        res = supabase.table("song_features").select("song_id").execute()
        processed_ids = {row['song_id'] for row in (res.data or [])}
    except Exception as e:
        print(f"\n⚠️  처리된 곡 조회 실패 (모든 곡을 처리 대상으로 간주): {e}")
        processed_ids = set()
    
    print(f"✓ 처리된 곡: {len(processed_ids)}개")
    
    # 2. songs 테이블에서 raw_s3_key가 있는 모든 곡 가져오기
    print("\n[Step 2] songs 테이블에서 raw_s3_key가 있는 곡 조회 중...")
    all_song_ids = []
    start = 0
    step = 1000
    
    while True:
        res = (
            supabase.table("songs")
            .select("id, raw_s3_key")
            .not_.is_("raw_s3_key", "null")
            .neq("raw_s3_key", "")
            .range(start, start + step - 1)
            .execute()
        )
        
        batch = res.data or []
        all_song_ids.extend([s['id'] for s in batch if s.get('raw_s3_key')])
        
        if len(batch) < step:
            break
        start += step
    
    print(f"✓ raw_s3_key가 있는 곡: {len(all_song_ids)}개")
    
    # 3. 처리되지 않은 곡 필터링
    unprocessed_ids = [sid for sid in all_song_ids if sid not in processed_ids]
    
    if limit:
        unprocessed_ids = unprocessed_ids[:limit]
    
    print(f"\n✓ 처리되지 않은 곡: {len(unprocessed_ids)}개")
    
    return unprocessed_ids


def save_features_to_db(song_id: str, features: Dict, features_s3_key: Optional[str] = None) -> None:
    """
    특징 추출 결과를 DB에 저장 (tj_to_db.py처럼 supabase 클라이언트 직접 사용)
    
    Args:
        song_id: 곡 ID (UUID)
        features: 특징 딕셔너리 (extract_song_features의 반환값)
        features_s3_key: 전체 JSON을 S3에 업로드한 경우의 키 (선택)
    """
    supabase = get_supabase_client()
    
    # embedding 벡터 추출 (192차원)
    song_repr_embedding = np.array(features['song_repr_embedding'])
    if len(song_repr_embedding) != 192:
        raise ValueError(f"임베딩 차원이 192가 아닙니다: {len(song_repr_embedding)}")
    
    # F0 퍼센타일
    f0_p5 = features['f0_p5']
    f0_p25 = features['f0_p25']
    f0_p50 = features.get('f0_p50', None)  # nullable
    f0_p75 = features['f0_p75']
    f0_p95 = features['f0_p95']
    voiced_ratio = features['voiced_ratio']
    
    # 음색 피처
    timbre = features['timbre']
    timbre_brightness = timbre['brightness']
    timbre_roughness = timbre['roughness']
    timbre_body = timbre['body']
    timbre_clarity = timbre['clarity']
    timbre_warmth = timbre['warmth']
    timbre_f0_mean = timbre['f0_mean']
    timbre_formant_f1 = timbre['formant_f1']
    timbre_formant_f2 = timbre['formant_f2']
    timbre_spectral_centroid = timbre['spectral_centroid']
    
    # vector 타입을 문자열로 변환 (pgvector 형식: '[1,2,3]')
    embedding_list = song_repr_embedding.tolist()
    embedding_str = '[' + ','.join(str(x) for x in embedding_list) + ']'
    
    # tj_to_db.py처럼 supabase 클라이언트로 RPC 함수 호출
    # (vector 타입은 RPC 함수를 통해 처리)
    try:
        # RPC 함수 호출 (tj_to_db.py의 supabase.table(...).execute() 패턴과 동일)
        supabase.rpc(
            'save_song_features',
            {
                'p_song_id': song_id,
                'p_embedding': embedding_str,
                'p_f0_p5': f0_p5,
                'p_f0_p25': f0_p25,
                'p_f0_p50': f0_p50,
                'p_f0_p75': f0_p75,
                'p_f0_p95': f0_p95,
                'p_voiced_ratio': voiced_ratio,
                'p_timbre_brightness': timbre_brightness,
                'p_timbre_roughness': timbre_roughness,
                'p_timbre_body': timbre_body,
                'p_timbre_clarity': timbre_clarity,
                'p_timbre_warmth': timbre_warmth,
                'p_timbre_f0_mean': timbre_f0_mean,
                'p_timbre_formant_f1': timbre_formant_f1,
                'p_timbre_formant_f2': timbre_formant_f2,
                'p_timbre_spectral_centroid': timbre_spectral_centroid,
                'p_features_s3_key': features_s3_key
            }
        ).execute()
        print(f"✓ DB 저장 완료: song_id={song_id}")
    except Exception as e:
        error_msg = str(e)
        
        # RPC 함수가 없는 경우 안내
        if "function" in error_msg.lower() and "does not exist" in error_msg.lower():
            sql_file = Path(__file__).parent / "create_save_song_features_rpc.sql"
            raise RuntimeError(
                f"\n❌ RPC 함수 'save_song_features'가 없습니다.\n"
                f"\n해결 방법:\n"
                f"1. Supabase 대시보드 → SQL Editor로 이동\n"
                f"2. 다음 파일의 SQL을 복사해서 실행:\n"
                f"   {sql_file}\n"
                f"\nRPC 함수 생성 후 다시 시도하세요!"
            ) from e
        
        # 기타 에러
        raise RuntimeError(f"DB 저장 실패: {error_msg}") from e


def load_features_from_json(json_path: str) -> Dict:
    """
    이미 추출된 특징 JSON 파일을 로드
    
    Args:
        json_path: JSON 파일 경로
    
    Returns:
        features: 특징 딕셔너리
    """
    json_path_obj = Path(json_path)
    if not json_path_obj.exists():
        raise FileNotFoundError(f"JSON 파일을 찾을 수 없습니다: {json_path}")
    
    with open(json_path_obj, 'r', encoding='utf-8') as f:
        features = json.load(f)
    
    print(f"✓ JSON 파일 로드 완료: {json_path}")
    return features


def save_features_from_json_to_db(json_path: str, upload_to_s3: bool = False) -> Dict:
    """
    이미 추출된 특징 JSON 파일을 읽어서 DB에만 저장 (재추출 없음)
    
    Args:
        json_path: JSON 파일 경로
        upload_to_s3: JSON 파일을 S3에 업로드할지 여부
    
    Returns:
        result: {
            'status': 'success' or 'failed',
            'song_id': song_id,
            'features_s3_key': S3 키 (업로드한 경우),
            'error': 에러 메시지 (실패 시)
        }
    """
    try:
        # JSON 파일 로드
        features = load_features_from_json(json_path)
        song_id = features.get('song_id')
        
        if not song_id:
            raise ValueError("JSON 파일에 'song_id'가 없습니다.")
        
        print(f"\n[DB 저장만 수행] song_id={song_id}")
        print(f"  - 특징 재추출 없이 JSON 파일에서 로드하여 DB에 저장")
        
        # S3 업로드 (선택적)
        features_s3_key = None
        if upload_to_s3:
            print("\n[Step 1] 특징 JSON S3 업로드")
            if not S3_BUCKET:
                raise RuntimeError("S3_BUCKET_NAME이 .env에 필요합니다.")
            
            json_path_obj = Path(json_path)
            features_s3_key = f"features/songs/{song_id}.json"
            s3 = boto3.client("s3")
            s3.upload_file(
                str(json_path_obj),
                S3_BUCKET,
                features_s3_key
            )
            print(f"✓ S3 업로드 완료: s3://{S3_BUCKET}/{features_s3_key}")
        
        # DB에 저장
        print("\n[Step 2] DB에 저장")
        save_features_to_db(song_id, features, features_s3_key)
        
        return {
            'status': 'success',
            'song_id': song_id,
            'features_s3_key': features_s3_key
        }
        
    except Exception as e:
        print(f"\n❌ 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'status': 'failed',
            'song_id': features.get('song_id', 'unknown') if 'features' in locals() else 'unknown',
            'error': str(e)
        }


def save_features_from_json_dir_to_db(json_dir: str, upload_to_s3: bool = False) -> List[Dict]:
    """
    디렉토리 내의 모든 JSON 파일을 읽어서 DB에 저장
    
    Args:
        json_dir: JSON 파일들이 있는 디렉토리
        upload_to_s3: JSON 파일을 S3에 업로드할지 여부
    
    Returns:
        results: 처리 결과 리스트
    """
    json_dir_path = Path(json_dir)
    if not json_dir_path.exists():
        raise ValueError(f"디렉토리가 없습니다: {json_dir}")
    
    # JSON 파일 찾기
    json_files = list(json_dir_path.glob("*.json"))
    
    if not json_files:
        raise ValueError(f"JSON 파일을 찾을 수 없습니다: {json_dir}")
    
    print(f"\n📋 총 {len(json_files)}개 JSON 파일 발견")
    
    results = []
    for i, json_file in enumerate(json_files, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(json_files)}] {json_file.name}")
        print(f"{'='*70}")
        
        result = save_features_from_json_to_db(str(json_file), upload_to_s3=upload_to_s3)
        results.append(result)
    
    # 배치 요약
    print("\n" + "="*70)
    print("📊 배치 처리 완료")
    print("="*70)
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"✅ 성공: {success_count}/{len(json_files)}")
    print(f"❌ 실패: {len(json_files) - success_count}/{len(json_files)}")
    print("="*70 + "\n")
    
    return results


def hz_to_midi(hz: float) -> float:
    """Hz를 MIDI note number로 변환"""
    if hz <= 0:
        return 0.0
    return 12 * np.log2(hz / 440.0) + 69.0


def estimate_bpm(audio: np.ndarray, sr: int) -> Dict:
    """
    BPM 추정 (원곡 전체에서)
    
    Args:
        audio: 오디오 신호
        sr: 샘플레이트
    
    Returns:
        bpm_info: {bpm, confidence}
    """
    try:
        # librosa tempo 추정
        tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
        
        # librosa 버전에 따라 tempo가 array일 수 있음 (안정적 처리)
        if isinstance(tempo, (np.ndarray, list)):
            tempo = float(np.squeeze(tempo)[0] if len(np.squeeze(tempo)) > 0 else 0.0)
        else:
            tempo = float(tempo)
        
        # 유효성 검사 (0보다 커야 함)
        if tempo <= 0 or not np.isfinite(tempo):
            print(f"⚠️  BPM 추정값이 유효하지 않음: {tempo}")
            return {
                'bpm': 0.0,
                'confidence': 0.0
            }
        
        bpm = tempo
        
        # 신뢰도는 beats의 일관성으로 근사
        if len(beats) > 1:
            beat_intervals = np.diff(beats)
            consistency = 1.0 - (np.std(beat_intervals) / np.mean(beat_intervals)) if np.mean(beat_intervals) > 0 else 0.0
            confidence = float(np.clip(consistency, 0.0, 1.0))
        else:
            confidence = 0.5
        
        print(f"✓ BPM 추정: {bpm:.1f} (신뢰도: {confidence:.2f})")
        
        return {
            'bpm': bpm,
            'confidence': confidence
        }
    except Exception as e:
        print(f"⚠️  BPM 추정 실패: {e}")
        return {
            'bpm': 0.0,
            'confidence': 0.0
        }


def estimate_key(audio: np.ndarray, sr: int) -> Dict:
    """
    Key 추정 (원곡 전체에서)
    
    Args:
        audio: 오디오 신호
        sr: 샘플레이트
    
    Returns:
        key_info: {key, confidence}
    """
    try:
        # Chroma feature 추출
        chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        
        # Key 추정 (간단한 방법)
        # 실제로는 keyfinder 같은 라이브러리를 사용하는 게 더 정확하지만,
        # 여기서는 chroma의 최대값으로 근사
        key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key_idx = int(np.argmax(chroma_mean))
        key = key_names[key_idx]
        
        # Major/Minor 구분은 간단히 chroma 패턴으로
        # 실제로는 더 정교한 방법이 필요하지만, 일단 major로 가정
        key_full = f"{key} major"
        
        confidence = float(chroma_mean[key_idx] / np.sum(chroma_mean)) if np.sum(chroma_mean) > 0 else 0.0
        
        print(f"✓ Key 추정: {key_full} (신뢰도: {confidence:.2f})")
        
        return {
            'key': key_full,
            'confidence': confidence
        }
    except Exception as e:
        print(f"⚠️  Key 추정 실패: {e}")
        return {
            'key': 'Unknown',
            'confidence': 0.0
        }


def extract_song_features(
    song_path: str,
    song_id: str,
    output_dir: str = "artifacts/song_features",
    use_vocal_separation: bool = True
) -> Dict:
    """
    곡 특징 추출
    
    Args:
        song_path: 원본 곡 파일 경로
        song_id: 곡 ID
        output_dir: 출력 디렉토리
        use_vocal_separation: 보컬 분리 사용 여부
    
    Returns:
        features: 곡 특징 딕셔너리
    """
    print("\n" + "="*70)
    print(f"🎵 곡 특징 추출: {song_id}")
    print("="*70)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 1. 원본 오디오 로드 (메타데이터 확인용)
    print("\n[Step 1] 원본 오디오 로드")
    audio_full, sr_full = librosa.load(song_path, sr=None, mono=True)
    print(f"✓ 로드 완료: {len(audio_full) / sr_full:.2f}초, {sr_full}Hz")
    
    # 2. 보컬 분리 (정교함 우선)
    if use_vocal_separation:
        print("\n[Step 2] 보컬 분리 (Demucs)")
        vocals_path = remove_mr(
            audio_path=song_path,
            output_dir=str(output_path / "vocals_temp")
        )
        vocals_path = str(vocals_path)
        
        # 안전장치: Demucs가 실제로 보컬 파일을 만들었는지 확인
        vocals_path_obj = Path(vocals_path)
        if not vocals_path_obj.exists():
            raise RuntimeError(
                f"Demucs 출력 파일이 존재하지 않습니다: {vocals_path}\n"
                f"보컬 분리가 실패했을 가능성이 높습니다."
            )
        
        # 안전장치: 원본 파일과 동일한 경로인지 확인 (버그 감지)
        if vocals_path_obj.resolve() == Path(song_path).resolve():
            raise RuntimeError(
                f"Demucs가 원본 파일 경로를 반환했습니다 (버그): {vocals_path}\n"
                f"보컬 분리가 실패했지만 성공한 척 하고 있습니다.\n"
                f"원인: Demucs ImportError 또는 Exception 발생 후 fallback"
            )
        
        # 안전장치: 파일 확장자 확인 (wav/flac/mp3/m4a여야 함)
        valid_extensions = [".wav", ".flac", ".mp3", ".m4a"]
        if vocals_path_obj.suffix.lower() not in valid_extensions:
            raise RuntimeError(
                f"Demucs 출력 파일 확장자가 유효하지 않습니다: {vocals_path}\n"
                f"예상 확장자: {valid_extensions}"
            )
        
        print(f"✓ 보컬 분리 완료: {vocals_path}")
        print(f"  ✓ 파일 존재 확인: OK")
        print(f"  ✓ 원본과 다른 경로 확인: OK")
        
        # 보컬 오디오 로드
        audio_vocals, sr_vocals = librosa.load(vocals_path, sr=16000, mono=True)
    else:
        # 보컬 분리 없이 원본 사용
        print("\n[Step 2] 보컬 분리 스킵 (원본 사용)")
        audio_vocals = librosa.resample(audio_full, orig_sr=sr_full, target_sr=16000)
        sr_vocals = 16000
    
    # 3. 전처리 및 세그먼트 생성
    print("\n[Step 3] 전처리 및 세그먼트 생성")
    preprocessor = AudioPreprocessor(
        target_sr=16000,
        segment_duration=15.0,  # 곡은 15초 세그먼트
        hop_duration=7.5         # 7.5초 hop
    )
    # 이미 16kHz로 리샘플링된 오디오를 표준화
    audio_std = preprocessor.standardize(audio_vocals, sr_vocals)
    segments = preprocessor.create_segments(audio_std)
    print(f"✓ 세그먼트 생성: {len(segments)}개")
    
    # 4. 특징 추출
    print("\n[Step 4] 특징 추출")
    extractor = FeatureExtractor(sr=16000)
    
    # 4-1. ECAPA 임베딩
    print("  - ECAPA 임베딩 추출 중...")
    embedding_features = extractor.extract_ecapa_embedding(segments, max_segments=10)
    song_repr_embedding = np.array(embedding_features['representative'])
    song_seg_embeddings = [np.array(emb) for emb in embedding_features['segment_embeddings']]
    
    # L2 normalize
    song_repr_embedding = song_repr_embedding / (np.linalg.norm(song_repr_embedding) + 1e-8)
    song_seg_embeddings = [emb / (np.linalg.norm(emb) + 1e-8) for emb in song_seg_embeddings]
    
    # 4-2. F0 추출 및 통계 (voiced 구간만 사용)
    print("  - F0 추출 중...")
    pitch_features = extractor.extract_pitch(audio_std, segments)
    
    # voiced 구간만 필터링 (f0 > 0이고 voiced_mask가 True인 것만)
    f0_contour = np.array(pitch_features['f0_contour'])
    voiced_mask = np.array(pitch_features.get('voiced_mask', f0_contour > 0))
    f0_voiced = f0_contour[(f0_contour > 0) & voiced_mask]
    
    # voiced_ratio 계산 (voiced_mask에서 직접 계산)
    if len(voiced_mask) > 0:
        voiced_ratio = float(np.sum(voiced_mask) / len(voiced_mask))
    else:
        voiced_ratio = 0.0
    
    # voiced_ratio가 너무 낮은 경우 경고
    if voiced_ratio < 0.3:
        print(f"  ⚠️  voiced_ratio가 낮습니다: {voiced_ratio:.2f} (0.3 미만)")
    
    if len(f0_voiced) > 0:
        f0_p5 = float(np.percentile(f0_voiced, 5))
        f0_p25 = float(np.percentile(f0_voiced, 25))
        f0_p50 = float(np.percentile(f0_voiced, 50))
        f0_p75 = float(np.percentile(f0_voiced, 75))
        f0_p95 = float(np.percentile(f0_voiced, 95))
        
        # MIDI 변환 (참고용, 저장은 Hz로)
        f0_p5_midi = hz_to_midi(f0_p5)
        f0_p25_midi = hz_to_midi(f0_p25)
        f0_p50_midi = hz_to_midi(f0_p50)
        f0_p75_midi = hz_to_midi(f0_p75)
        f0_p95_midi = hz_to_midi(f0_p95)
    else:
        f0_p5 = f0_p25 = f0_p50 = f0_p75 = f0_p95 = 0.0
        f0_p5_midi = f0_p25_midi = f0_p50_midi = f0_p75_midi = f0_p95_midi = 0.0
        voiced_ratio = 0.0
    
    # 4-3. 음색 피처
    print("  - 음색 피처 추출 중...")
    timbre_features = extractor.extract_timbre(audio_std, segments)
    timbre_weighted = timbre_features['weighted']
    
    # 5. 결과 구성
    from datetime import datetime
    
    features = {
        # 메타데이터
        'schema_version': '1.0',
        'created_at': datetime.now().isoformat(),
        'song_id': song_id,
        'song_path': str(song_path),
        
        # 세그먼트 설정
        'segment_config': {
            'window_sec': 15.0,
            'hop_sec': 7.5,
            'sr': 16000
        },
        
        # 소스 정보
        'source': {
            'original_path': str(song_path),
            'vocals_path': str(vocals_path) if use_vocal_separation else None,
            'demucs_model': 'htdemucs' if use_vocal_separation else None
        },
        
        # ECAPA 임베딩
        'song_repr_embedding': song_repr_embedding.tolist(),
        'song_seg_embeddings': [emb.tolist() for emb in song_seg_embeddings],
        'embedding_dim': int(song_repr_embedding.shape[0]),
        
        # 음역대 (F0 퍼센타일)
        'f0_p5': f0_p5,
        'f0_p25': f0_p25,
        'f0_p50': f0_p50,
        'f0_p75': f0_p75,
        'f0_p95': f0_p95,
        'f0_p5_midi': f0_p5_midi,
        'f0_p25_midi': f0_p25_midi,
        'f0_p50_midi': f0_p50_midi,
        'f0_p75_midi': f0_p75_midi,
        'f0_p95_midi': f0_p95_midi,
        'voiced_ratio': voiced_ratio,
        
        # 음색 프로파일
        'timbre': {
            'brightness': float(timbre_weighted.get('brightness', 0.0)),
            'roughness': float(timbre_weighted.get('roughness', 0.0)),
            'body': float(timbre_weighted.get('body', 0.0)),
            'clarity': float(timbre_weighted.get('clarity', 0.0)),
            'warmth': float(timbre_weighted.get('warmth', 0.0)),
            'f0_mean': float(timbre_weighted.get('f0_mean', 0.0)),
            'formant_f1': float(timbre_weighted.get('formant_f1', 0.0)),
            'formant_f2': float(timbre_weighted.get('formant_f2', 0.0)),
            'spectral_centroid': float(timbre_weighted.get('spectral_centroid', 0.0))
        },
        
        # 메타데이터
        'num_segments': len(segments),
        'duration': len(audio_std) / 16000.0
    }
    
    # 7. 저장
    output_file = output_path / f"{song_id}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(features, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ 특징 저장 완료: {output_file}")
    print("="*70 + "\n")
    
    return features


def process_songs_batch(
    songs_dir: str,
    output_dir: str = "artifacts/song_features",
    use_vocal_separation: bool = True
) -> list:
    """
    여러 곡을 배치로 처리
    
    Args:
        songs_dir: 곡 파일들이 있는 디렉토리
        output_dir: 출력 디렉토리
        use_vocal_separation: 보컬 분리 사용 여부
    
    Returns:
        results: 처리 결과 리스트
    """
    songs_path = Path(songs_dir)
    if not songs_path.exists():
        raise ValueError(f"곡 디렉토리가 없습니다: {songs_dir}")
    
    # 지원하는 오디오 포맷
    audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.mp4']
    
    # 곡 파일 찾기
    song_files = []
    for ext in audio_extensions:
        song_files.extend(list(songs_path.glob(f"*{ext}")))
    
    if not song_files:
        raise ValueError(f"곡 파일을 찾을 수 없습니다: {songs_dir}")
    
    print(f"\n📋 총 {len(song_files)}개 곡 발견")
    
    results = []
    for i, song_file in enumerate(song_files, 1):
        song_id = song_file.stem  # 파일명에서 확장자 제거
        
        print(f"\n{'='*70}")
        print(f"[{i}/{len(song_files)}] {song_file.name}")
        print(f"{'='*70}")
        
        try:
            features = extract_song_features(
                song_path=str(song_file),
                song_id=song_id,
                output_dir=output_dir,
                use_vocal_separation=use_vocal_separation
            )
            results.append({
                'song_id': song_id,
                'status': 'success',
                'features': features
            })
        except Exception as e:
            print(f"❌ 처리 실패: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'song_id': song_id,
                'status': 'failed',
                'error': str(e)
            })
    
    # 배치 요약
    print("\n" + "="*70)
    print("📊 배치 처리 완료")
    print("="*70)
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"✅ 성공: {success_count}/{len(song_files)}")
    print(f"❌ 실패: {len(song_files) - success_count}/{len(song_files)}")
    print("="*70 + "\n")
    
    return results


def process_song_from_s3(
    song_id: str,
    raw_s3_key: Optional[str] = None,
    output_dir: Optional[str] = None,
    use_vocal_separation: bool = True,
    save_to_db: bool = True,
    upload_features_to_s3: bool = False
) -> Dict:
    """
    S3에서 곡을 다운로드하여 특징 추출 후 DB에 저장
    
    Args:
        song_id: 곡 ID (UUID)
        raw_s3_key: S3에 저장된 원본 음원 키 (None이면 DB에서 조회)
        output_dir: 임시 파일 저장 디렉토리 (None이면 임시 디렉토리 사용)
        use_vocal_separation: 보컬 분리 사용 여부
        save_to_db: DB에 저장 여부
        upload_features_to_s3: 전체 JSON을 S3에 업로드할지 여부
    
    Returns:
        result: {
            'status': 'success' or 'failed',
            'song_id': song_id,
            'features': 특징 딕셔너리 (성공 시),
            'error': 에러 메시지 (실패 시)
        }
    """
    print("\n" + "="*70)
    print(f"🎵 곡 특징 추출 시작: song_id={song_id}")
    print("="*70)
    
    # 임시 디렉토리 생성
    if output_dir is None:
        temp_dir = Path(tempfile.mkdtemp(prefix=f"song_feature_{song_id}_"))
    else:
        temp_dir = Path(output_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: DB에서 곡 정보 조회 (raw_s3_key가 없는 경우)
        if raw_s3_key is None:
            print("\n[Step 1] DB에서 곡 정보 조회")
            song_info = get_song_from_db(song_id)
            if not song_info:
                raise ValueError(f"곡을 찾을 수 없습니다: song_id={song_id}")
            
            raw_s3_key = song_info.get('raw_s3_key')
            if not raw_s3_key:
                raise ValueError(f"raw_s3_key가 없습니다: song_id={song_id}")
            
            title = song_info.get('title', 'Unknown')
            artist = song_info.get('artist', 'Unknown')
            print(f"✓ 곡 정보 조회 완료: {title} - {artist}")
            print(f"  - raw_s3_key: {raw_s3_key}")
        else:
            print("\n[Step 1] S3 키 직접 지정")
            print(f"  - raw_s3_key: {raw_s3_key}")
        
        # Step 2: S3에서 음원 다운로드
        print("\n[Step 2] S3에서 음원 다운로드")
        if not S3_BUCKET:
            raise RuntimeError("S3_BUCKET_NAME이 .env에 필요합니다.")
        
        local_audio_path = temp_dir / f"{song_id}_raw.mp4"
        s3_download(S3_BUCKET, raw_s3_key, local_audio_path)
        print(f"✓ 다운로드 완료: {local_audio_path}")
        
        # Step 3: 특징 추출
        print("\n[Step 3] 특징 추출")
        features = extract_song_features(
            song_path=str(local_audio_path),
            song_id=song_id,
            output_dir=str(temp_dir / "features"),
            use_vocal_separation=use_vocal_separation
        )
        
        # Step 4: 선택적으로 전체 JSON을 S3에 업로드
        features_s3_key = None
        if upload_features_to_s3:
            print("\n[Step 4] 특징 JSON S3 업로드")
            features_json_path = temp_dir / "features" / f"{song_id}.json"
            if features_json_path.exists():
                features_s3_key = f"features/songs/{song_id}.json"
                s3 = boto3.client("s3")
                s3.upload_file(
                    str(features_json_path),
                    S3_BUCKET,
                    features_s3_key
                )
                print(f"✓ S3 업로드 완료: s3://{S3_BUCKET}/{features_s3_key}")
        
        # Step 5: DB에 저장
        features_json_path = None
        if save_to_db:
            print("\n[Step 5] DB에 저장")
            # JSON 파일 경로 저장 (실패 시 재시도용)
            features_json_path = temp_dir / "features" / f"{song_id}.json"
            try:
                save_features_to_db(song_id, features, features_s3_key)
            except Exception as db_error:
                # DB 저장 실패 시 JSON 파일 경로 출력 및 재시도 방법 안내
                print(f"\n❌ DB 저장 실패: {db_error}")
                print("\n" + "="*70)
                print("💡 Step 5 (DB 저장)만 재시도하는 방법:")
                print("="*70)
                if features_json_path and features_json_path.exists():
                    print(f"\n다음 명령어로 DB 저장만 다시 시도하세요:")
                    print(f"\n  python song_feature_worker.py --from-json \"{features_json_path}\"")
                    print(f"\n또는 JSON 파일을 다른 위치로 복사한 후:")
                    print(f"  cp \"{features_json_path}\" artifacts/song_features/{song_id}.json")
                    print(f"  python song_feature_worker.py --from-json artifacts/song_features/{song_id}.json")
                else:
                    print(f"\n⚠️  JSON 파일을 찾을 수 없습니다: {features_json_path}")
                print("="*70 + "\n")
                raise  # 에러를 다시 발생시켜서 실패 상태로 반환
        
        print("\n" + "="*70)
        print(f"✅ 곡 특징 추출 완료: song_id={song_id}")
        print("="*70)
        
        return {
            'status': 'success',
            'song_id': song_id,
            'features': features,
            'features_s3_key': features_s3_key,
            'features_json_path': str(features_json_path) if features_json_path else None
        }
        
    except Exception as e:
        print(f"\n❌ 곡 특징 추출 실패: {e}")
        import traceback
        traceback.print_exc()
        
        # JSON 파일 경로 확인 (특징 추출은 성공했지만 DB 저장만 실패한 경우)
        features_json_path = None
        if 'temp_dir' in locals():
            features_json_path = temp_dir / "features" / f"{song_id}.json"
            if features_json_path.exists():
                print("\n" + "="*70)
                print("💡 특징 추출은 완료되었습니다. Step 5 (DB 저장)만 재시도하세요:")
                print("="*70)
                print(f"\n  python song_feature_worker.py --from-json \"{features_json_path}\"")
                print("="*70 + "\n")
        
        return {
            'status': 'failed',
            'song_id': song_id,
            'error': str(e),
            'features_json_path': str(features_json_path) if features_json_path and features_json_path.exists() else None
        }
    
    finally:
        # 임시 파일 정리 (선택적 - 디버깅 시 남겨둘 수 있음)
        # temp_dir의 파일들을 삭제하려면 여기서 처리
        pass


def process_songs_from_db(
    song_ids: List[str],
    use_vocal_separation: bool = True,
    save_to_db: bool = True,
    upload_features_to_s3: bool = False
) -> List[Dict]:
    """
    DB에서 곡 정보를 가져와서 배치 처리
    
    Args:
        song_ids: 곡 ID 리스트
        use_vocal_separation: 보컬 분리 사용 여부
        save_to_db: DB에 저장 여부
        upload_features_to_s3: 전체 JSON을 S3에 업로드할지 여부
    
    Returns:
        results: 처리 결과 리스트
    """
    print(f"\n📋 총 {len(song_ids)}개 곡 처리 시작")
    
    results = []
    for i, song_id in enumerate(song_ids, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(song_ids)}] song_id={song_id}")
        print(f"{'='*70}")
        
        result = process_song_from_s3(
            song_id=song_id,
            raw_s3_key=None,  # DB에서 조회
            use_vocal_separation=use_vocal_separation,
            save_to_db=save_to_db,
            upload_features_to_s3=upload_features_to_s3
        )
        results.append(result)
    
    # 배치 요약
    print("\n" + "="*70)
    print("📊 배치 처리 완료")
    print("="*70)
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"✅ 성공: {success_count}/{len(song_ids)}")
    print(f"❌ 실패: {len(song_ids) - success_count}/{len(song_ids)}")
    print("="*70 + "\n")
    
    return results


# CLI 실행
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="노래 분석 워커 (곡 특징 추출 및 DB 저장)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 단일 곡 테스트 (가장 간단)
  python song_feature_worker.py --song-id <song_id>
  
  # 여러 곡 배치 처리
  python song_feature_worker.py --song-ids <id1> <id2> <id3>
  
  # 로컬 파일 모드
  python song_feature_worker.py --mode local --songs-dir ./songs
        """
    )
    
    # 모드 선택: 로컬 파일 vs S3+DB
    parser.add_argument(
        "--mode",
        type=str,
        choices=["local", "s3"],
        default="s3",
        help="처리 모드: local (로컬 파일) 또는 s3 (S3 다운로드 + DB 저장, 기본값)"
    )
    
    # 로컬 파일 모드
    parser.add_argument(
        "--songs-dir",
        type=str,
        dest="songs_dir",
        help="곡 파일들이 있는 디렉토리 (--mode local일 때 필수)"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="artifacts/song_features",
        help="출력 디렉토리 (기본값: artifacts/song_features)"
    )
    
    # S3+DB 모드
    parser.add_argument(
        "--song-id",
        type=str,
        dest="song_id",
        help="처리할 곡 ID (UUID, --mode s3일 때 필수)"
    )
    parser.add_argument(
        "--song-ids",
        type=str,
        nargs="+",
        dest="song_ids",
        help="처리할 곡 ID 리스트 (UUID, --mode s3일 때 --song-id 대신 사용 가능)"
    )
    parser.add_argument(
        "--unprocessed",
        action="store_true",
        help="처리되지 않은 모든 곡을 자동으로 가져와서 처리 (--mode s3일 때)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="처리할 최대 곡 개수 (--unprocessed와 함께 사용)"
    )
    parser.add_argument(
        "--raw-s3-key",
        type=str,
        dest="raw_s3_key",
        help="직접 S3 키 지정 (--song-id와 함께 사용, DB 조회 스킵)"
    )
    parser.add_argument(
        "--no-vocal-separation",
        action="store_true",
        help="보컬 분리 스킵 (원본 사용)"
    )
    parser.add_argument(
        "--no-save-db",
        action="store_true",
        help="DB 저장 스킵 (테스트용)"
    )
    parser.add_argument(
        "--upload-features-s3",
        action="store_true",
        help="전체 특징 JSON을 S3에 업로드"
    )
    parser.add_argument(
        "--from-json",
        type=str,
        dest="from_json",
        help="이미 추출된 JSON 파일 경로 (재추출 없이 DB 저장만)"
    )
    parser.add_argument(
        "--from-json-dir",
        type=str,
        dest="from_json_dir",
        help="JSON 파일들이 있는 디렉토리 (재추출 없이 DB 저장만)"
    )
    
    args = parser.parse_args()
    
    try:
        # JSON 파일에서 DB 저장만 하는 모드 (최우선)
        if args.from_json or args.from_json_dir:
            if args.from_json and args.from_json_dir:
                print("❌ --from-json과 --from-json-dir를 동시에 사용할 수 없습니다")
                exit(1)
            
            if not SUPABASE_URL or not SUPABASE_KEY:
                print("❌ SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY가 .env에 필요합니다.")
                exit(1)
            
            if args.from_json:
                # 단일 JSON 파일
                result = save_features_from_json_to_db(
                    args.from_json,
                    upload_to_s3=args.upload_features_s3
                )
                if result['status'] == 'success':
                    print("\n✅ DB 저장 완료!")
                    exit(0)
                else:
                    print(f"\n❌ DB 저장 실패: {result.get('error', 'Unknown error')}")
                    exit(1)
            else:
                # JSON 디렉토리
                results = save_features_from_json_dir_to_db(
                    args.from_json_dir,
                    upload_to_s3=args.upload_features_s3
                )
                success_count = sum(1 for r in results if r['status'] == 'success')
                if success_count == len(results):
                    print("\n✅ 모든 JSON 파일 DB 저장 완료!")
                    exit(0)
                else:
                    print(f"\n⚠️  일부 JSON 파일 DB 저장 실패: {success_count}/{len(results)} 성공")
                    exit(1)
        
        elif args.mode == "local":
            # 로컬 파일 모드
            if not args.songs_dir:
                print("❌ --songs_dir이 필요합니다 (--mode local일 때)")
                exit(1)
            
            results = process_songs_batch(
                songs_dir=args.songs_dir,
                output_dir=args.out,
                use_vocal_separation=not args.no_vocal_separation
            )
            
            print("\n✅ 처리 완료!")
            
        else:  # mode == "s3"
            # S3+DB 모드
            if not args.song_id and not args.song_ids and not args.unprocessed:
                print("❌ --song-id, --song-ids, 또는 --unprocessed 중 하나가 필요합니다 (--mode s3일 때)")
                exit(1)
            
            # 옵션 충돌 체크
            option_count = sum([bool(args.song_id), bool(args.song_ids), bool(args.unprocessed)])
            if option_count > 1:
                print("❌ --song-id, --song-ids, --unprocessed 중 하나만 사용할 수 있습니다")
                exit(1)
            
            # 필수 체크
            if not S3_BUCKET:
                print("❌ S3_BUCKET_NAME이 .env에 필요합니다.")
                exit(1)
            
            # Supabase 클라이언트 사용 (REST API를 통해 접근)
            if not SUPABASE_URL or not SUPABASE_KEY:
                print("❌ SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY가 .env에 필요합니다.")
                exit(1)
            
            # DB 저장을 위한 PostgreSQL 연결 정보도 필요
            if not args.no_save_db:
                if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
                    print("❌ DB 연결 정보가 .env에 필요합니다: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
                    print("   (song_features 테이블 저장용)")
                    exit(1)
            
            if not args.no_save_db:
                if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
                    print("❌ DB 연결 정보가 .env에 필요합니다: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
                    print("   (Supabase의 직접 PostgreSQL 연결 정보)")
                    exit(1)
            
            if args.unprocessed:
                # 처리되지 않은 곡 자동 가져오기
                print("\n[모드] 처리되지 않은 곡 자동 처리")
                song_ids = get_unprocessed_song_ids(limit=args.limit)
                
                if not song_ids:
                    print("\n✅ 처리할 곡이 없습니다!")
                    exit(0)
                
                print(f"\n📋 총 {len(song_ids)}개 곡을 처리합니다.")
                results = process_songs_from_db(
                    song_ids=song_ids,
                    use_vocal_separation=not args.no_vocal_separation,
                    save_to_db=not args.no_save_db,
                    upload_features_to_s3=args.upload_features_s3
                )
                
                success_count = sum(1 for r in results if r['status'] == 'success')
                if success_count == len(results):
                    print("\n✅ 모든 곡 처리 완료!")
                    exit(0)
                else:
                    print(f"\n⚠️  일부 곡 처리 실패: {success_count}/{len(results)} 성공")
                    exit(1)
            elif args.song_id:
                # 단일 곡 처리
                result = process_song_from_s3(
                    song_id=args.song_id,
                    raw_s3_key=args.raw_s3_key,
                    use_vocal_separation=not args.no_vocal_separation,
                    save_to_db=not args.no_save_db,
                    upload_features_to_s3=args.upload_features_s3
                )
                
                if result['status'] == 'success':
                    print("\n✅ 처리 완료!")
                    exit(0)
                else:
                    print(f"\n❌ 처리 실패: {result.get('error', 'Unknown error')}")
                    exit(1)
            else:
                # 배치 처리 (--song-ids 사용)
                results = process_songs_from_db(
                    song_ids=args.song_ids,
                    use_vocal_separation=not args.no_vocal_separation,
                    save_to_db=not args.no_save_db,
                    upload_features_to_s3=args.upload_features_s3
                )
                
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


"""
추천 워커 (1차 + 2차 통합)

Queue에서 job_id, user_id, (선택) s3_key를 받아서:
1. 1차 추천: user_vocal_profiles(보컬 워커가 채운 스코어링 컬럼)로 유저 특징 로드 → 유저-음원 계산 → 상위 200곡 MongoDB basescore 저장
   (비상 폴백: FIRST_REC_FORCE_PIPELINE=1 이면 S3+s3_key 로 파이프라인 재실행)
2. WAITING_FEEDBACK: 유저 피드백 대기 (기본은 여기서 종료; 2차는 SQS stage2 등 별도 트리거)
3. 2차 추천: 피드백 기반 재정렬 → recommend_songs 저장 (RECOMMENDATION_AUTO_STAGE2=1 이면 1차 직후 자동)

Status: QUEUED → RUNNING_STAGE1 → WAITING_FEEDBACK → RUNNING_STAGE2 → DONE/FAILED
"""
import json
import os
import time
from datetime import datetime
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

# 환경 변수
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")  # 추천 작업 Queue URL
MONGO_URI = os.getenv("MONGO_URI")  # MongoDB 연결 문자열
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "singchronize")  # MongoDB 데이터베이스 이름


def auto_run_stage2_after_stage1() -> bool:
    """
    True 이면 1차 직후 같은 프로세스에서 2차까지 실행 (구버전/통합 테스트용).
    기본 False — 앱 플로우: 1차 후 WAITING_FEEDBACK → 유저 피드백 HTTP 저장 → SQS stage2.
    환경변수: RECOMMENDATION_AUTO_STAGE2=1|true|yes
    """
    v = (os.getenv("RECOMMENDATION_AUTO_STAGE2") or "").strip().lower()
    return v in ("1", "true", "yes")


# Status 상수
STATUS_QUEUED = "QUEUED"
STATUS_RUNNING_STAGE1 = "RUNNING_STAGE1"
STATUS_WAITING_FEEDBACK = "WAITING_FEEDBACK"
# 백엔드가 피드백 반영 후 세팅 — SQS stage2 와 함께 쓰는 제품용 상태 (워커는 쓰지 않음)
STATUS_READY_FOR_STAGE2 = "READY_FOR_STAGE2"
STATUS_RUNNING_STAGE2 = "RUNNING_STAGE2"
STATUS_DONE = "DONE"
STATUS_FAILED = "FAILED"

# first_recommendation_worker 모듈 import
import sys
recommendation_path = Path(__file__).parent
sys.path.insert(0, str(recommendation_path))
from first_recommendation_worker import (
    get_supabase_client,
    s3_download,
    extract_user_features_from_audio,
    get_all_song_features_from_db,
    try_load_user_features_from_vocal_profile,
)

# scoring_runner 모듈 import
scoring_runner_path = Path(__file__).parent.parent
sys.path.insert(0, str(scoring_runner_path))
from scoring_runner import score_song


def get_mongo_client():
    """MongoDB 클라이언트 생성"""
    try:
        from pymongo import MongoClient
        if not MONGO_URI:
            raise RuntimeError("MONGO_URI가 .env에 설정되지 않았습니다.")
        
        client = MongoClient(MONGO_URI)
        print(f"✓ MongoDB 클라이언트 생성 성공")
        return client
    except ImportError:
        raise RuntimeError("pymongo가 설치되지 않았습니다. pip install pymongo")
    except Exception as e:
        raise RuntimeError(f"MongoDB 클라이언트 생성 실패: {e}") from e


def update_recommendation_status(
    supabase,
    job_id: str,
    status: str,
    error_message: Optional[str] = None
) -> None:
    """
    recommendation_logs 테이블의 status 업데이트
    
    Args:
        supabase: Supabase 클라이언트
        job_id: 작업 ID
        status: 상태 (QUEUED, RUNNING_STAGE1, WAITING_FEEDBACK, RUNNING_STAGE2, DONE, FAILED 등)
        error_message: 에러 메시지 (실패 시)
    """
    update_data = {
        'status': status,
        'updated_at': datetime.now().isoformat()
    }
    
    if status == STATUS_RUNNING_STAGE1:
        update_data['stage1_started_at'] = datetime.now().isoformat()
    elif status == STATUS_WAITING_FEEDBACK:
        update_data['stage1_completed_at'] = datetime.now().isoformat()
    elif status == STATUS_RUNNING_STAGE2:
        update_data['stage2_started_at'] = datetime.now().isoformat()
    elif status == STATUS_DONE:
        update_data['stage2_completed_at'] = datetime.now().isoformat()
    elif status == STATUS_FAILED:
        update_data['error_message'] = error_message
        update_data['failed_at'] = datetime.now().isoformat()
    
    try:
        supabase.table("recommendation_logs").update(update_data).eq("id", job_id).execute()
        print(f"✓ Status 업데이트: {status}")
    except Exception as e:
        print(f"⚠️  Status 업데이트 실패: {e}")


def get_song_info_from_db(supabase, song_id: str) -> Optional[Dict]:
    """
    songs 테이블에서 곡 정보 조회 (키워드, 장르 포함)
    
    Args:
        supabase: Supabase 클라이언트
        song_id: 곡 ID
    
    Returns:
        song_info: {id, title, artist, album_cover, genre, tags} 또는 None
    """
    try:
        res = (
            supabase.table("songs")
            .select("id, title, artist, album_cover, genre, tags")
            .eq("id", song_id)
            .execute()
        )
        
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception as e:
        print(f"⚠️  곡 정보 조회 실패 (song_id={song_id}): {e}")
        return None


def parse_genres(genre_str: Optional[str]) -> List[str]:
    """장르 문자열을 리스트로 파싱"""
    if not genre_str:
        return []
    
    if isinstance(genre_str, list):
        return [g.strip() for g in genre_str if g.strip()]
    
    if isinstance(genre_str, str):
        return [g.strip() for g in genre_str.split(',') if g.strip()]
    
    return []


def parse_situations(tags_str: Optional[str]) -> List[str]:
    """
    tags 필드에서 상황(situation) 추출
    
    Note: tags에는 상황 정보가 포함되어 있으며, 과거에는 짧은 라벨(회식/가족/친구/...)로 저장됐을 수 있습니다.
    여기서는 출력은 항상 이미지의 “상황 문구”로 정규화하고, 짧은 라벨은 alias로 매핑합니다.
    """
    if tags_str is None or tags_str == "":
        return []

    # tags는 jsonb로 저장돼 있을 수 있어, 문자열이면 JSON 파싱 시도
    if isinstance(tags_str, str):
        try:
            import json as _json

            parsed = _json.loads(tags_str)
            if isinstance(parsed, list):
                tags = parsed
            else:
                tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        except Exception:
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]
    elif isinstance(tags_str, list):
        tags = tags_str
    elif isinstance(tags_str, dict):
        tags = [tags_str]
    else:
        return []
    
    # canonical 상황 문구 (UI 표시용)
    SITUATION_KEYS = [
        "회식하며 즐길 때",
        "가족과 함께할 때",
        "친구랑 놀 때",
        "연인과 함께할 때",
        "공연을 준비할 때",
        "신나게 놀고 싶을 때",
        "감성에 젖고 싶을 때",
        "엔딩곡이 필요할 때",
    ]

    # 과거/호환 alias -> canonical
    SITUATION_ALIAS_TO_CANONICAL = {
        "회식": "회식하며 즐길 때",
        "가족": "가족과 함께할 때",
        "친구": "친구랑 놀 때",
        "연인": "연인과 함께할 때",
        "공연": "공연을 준비할 때",
        "신남": "신나게 놀고 싶을 때",
        "감성": "감성에 젖고 싶을 때",
        "엔딩": "엔딩곡이 필요할 때",
        # canonical 자체도 그대로 통과
        "회식하며 즐길 때": "회식하며 즐길 때",
        "가족과 함께할 때": "가족과 함께할 때",
        "친구랑 놀 때": "친구랑 놀 때",
        "연인과 함께할 때": "연인과 함께할 때",
        "공연을 준비할 때": "공연을 준비할 때",
        "신나게 놀고 싶을 때": "신나게 놀고 싶을 때",
        "감성에 젖고 싶을 때": "감성에 젖고 싶을 때",
        "엔딩곡이 필요할 때": "엔딩곡이 필요할 때",
    }

    situations: List[str] = []
    for item in tags:
        label: Optional[str] = None
        if isinstance(item, dict):
            # DB에 situationLabel로 저장되는 케이스
            label = (
                item.get("situationLabel")
                or item.get("label")
                or item.get("situation")
            )
        elif isinstance(item, str):
            label = item.strip()

        if not label:
            continue

        canonical = SITUATION_ALIAS_TO_CANONICAL.get(label)
        if canonical:
            situations.append(canonical)

    return situations


def save_basescore_to_mongodb(
    mongo_client,
    job_id: str,
    user_id: str,
    ranked_results: List[Dict],
    top_n: int = 200
) -> None:
    """
    상위 N개 곡의 basescore를 MongoDB에 저장
    
    Args:
        mongo_client: MongoDB 클라이언트
        job_id: 작업 ID
        user_id: 유저 ID
        ranked_results: 정렬된 점수 결과 리스트
        top_n: 저장할 상위 곡 개수 (기본값: 200)
    """
    from pymongo import MongoClient
    
    db = mongo_client[MONGO_DB_NAME]
    collection = db["basescores"]
    
    supabase = get_supabase_client()
    
    # 상위 N개만 선택
    top_results = ranked_results[:top_n]
    
    print(f"\n[MongoDB 저장] 상위 {len(top_results)}개 곡의 basescore 저장 중...")
    
    basescore_docs = []
    
    for result in top_results:
        song_id = result['song_id']
        
        # DB에서 곡 정보 조회 (키워드, 장르)
        song_info = get_song_info_from_db(supabase, song_id)
        
        if not song_info:
            print(f"  ⚠️  곡 정보를 찾을 수 없음: {song_id}")
            continue
        
        # 장르 파싱
        genres = parse_genres(song_info.get('genre', ''))
        
        # 상황 파싱
        situations = parse_situations(song_info.get('tags', ''))
        
        # 키워드 파싱 (tags 필드에서 상황 제외)
        # keywords는 상황 문구(또는 과거 alias)를 제외한 “나머지 tags”만 남긴다.
        SITUATION_ALIAS_KEYS = {
            '회식', '가족', '친구', '연인', '공연', '신남', '감성', '엔딩',
            "회식하며 즐길 때",
            "가족과 함께할 때",
            "친구랑 놀 때",
            "연인과 함께할 때",
            "공연을 준비할 때",
            "신나게 놀고 싶을 때",
            "감성에 젖고 싶을 때",
            "엔딩곡이 필요할 때",
        }
        tags = song_info.get('tags', '')
        label_candidates: List[str] = []

        if isinstance(tags, str):
            try:
                import json as _json

                parsed = _json.loads(tags)
                if isinstance(parsed, list):
                    tags_list = parsed
                else:
                    tags_list = []
            except Exception:
                tags_list = []

            if tags_list:
                for item in tags_list:
                    if isinstance(item, str):
                        label_candidates.append(item.strip())
                    elif isinstance(item, dict):
                        kw = item.get("keywordLabel") or item.get("label")
                        if isinstance(kw, str) and kw.strip():
                            label_candidates.append(kw.strip())
            else:
                if tags:
                    label_candidates.extend([t.strip() for t in tags.split(",") if t.strip()])

        elif isinstance(tags, list):
            for item in tags:
                if isinstance(item, str):
                    label_candidates.append(item.strip())
                elif isinstance(item, dict):
                    kw = item.get("keywordLabel") or item.get("label")
                    if isinstance(kw, str) and kw.strip():
                        label_candidates.append(kw.strip())

        keywords = [t for t in label_candidates if t not in SITUATION_ALIAS_KEYS]
        
        basescore_doc = {
            'job_id': job_id,
            'user_id': user_id,
            'song_id': song_id,
            'basescore': result['final_score'],
            'date': datetime.now().isoformat(),
            'genre': genres,
            'situations': situations,
            'keywords': keywords,
            'title': song_info.get('title', ''),
            'artist': song_info.get('artist', ''),
            # 상세 점수 정보 (선택적)
            'ecapa_score': result.get('ecapa_score', 0.0),
            'pitch_total': result.get('pitch_total', result.get('pitch_score', 0.0)),
            'timbre_score': result.get('timbre_score', 0.0),
            'created_at': datetime.now()
        }
        basescore_docs.append(basescore_doc)
    
    # MongoDB에 저장 (bulk insert)
    if basescore_docs:
        collection.insert_many(basescore_docs)
        print(f"✓ {len(basescore_docs)}개 basescore 저장 완료")
    else:
        print("⚠️  저장할 basescore가 없습니다.")


def process_stage1(
    job_id: str,
    user_id: str,
    s3_key: str = "",
) -> Dict:
    """
    1차 추천 처리 (RUNNING_STAGE1)

    기본: user_vocal_profiles 에서 스코어링 특징 로드 (보컬 분석 워커 완료 후).
    폴백: FIRST_REC_FORCE_PIPELINE=1 이고 s3_key 가 있으면 S3 다운로드 + 파이프라인.

    Args:
        job_id: 작업 ID
        user_id: 유저 ID
        s3_key: 폴백용 S3 오브젝트 키 (기본 경로에서는 생략 가능)

    Returns:
        result: 처리 결과
    """
    import shutil
    import tempfile

    print("\n" + "=" * 70)
    print(f"🎯 1차 추천 처리 시작 (Stage 1)")
    print("=" * 70)
    print(f"  - job_id: {job_id}")
    print(f"  - user_id: {user_id}")
    print(f"  - s3_key: {s3_key or '(없음, DB 프로필 사용)'}")
    print("=" * 70)

    supabase = get_supabase_client()
    mongo_client = get_mongo_client()

    # Status 업데이트: RUNNING_STAGE1
    update_recommendation_status(supabase, job_id, STATUS_RUNNING_STAGE1)

    temp_dir: Optional[Path] = None

    try:
        force_pipeline = os.getenv("FIRST_REC_FORCE_PIPELINE", "").lower() in (
            "1",
            "true",
            "yes",
        )

        if force_pipeline:
            print(
                "\n[Step 1-2] FIRST_REC_FORCE_PIPELINE: S3 + UserVocalPipeline "
                "(user_vocal_profiles 미사용)"
            )
            sk = (s3_key or "").strip()
            if not S3_BUCKET or not sk:
                raise RuntimeError(
                    "FIRST_REC_FORCE_PIPELINE=1 일 때는 S3_BUCKET_NAME 과 유효한 s3_key 가 필요합니다."
                )
            temp_dir = Path(tempfile.mkdtemp(prefix=f"recommendation_{job_id}_"))
            local_audio_path = temp_dir / f"{job_id}_user_audio.m4a"
            s3_download(S3_BUCKET, sk, local_audio_path)
            print(f"✓ 다운로드 완료: {local_audio_path}")
            print("\n[Step 2] 유저 특징 추출 (UserVocalPipeline)")
            user_features = extract_user_features_from_audio(
                audio_path=str(local_audio_path),
                output_dir=str(temp_dir / "user_features"),
            )
        else:
            print(
                "\n[Step 1-2] user_vocal_profiles 에서 스코어링 특징 로드 "
                "(보컬 분석 완료 후 저장된 값)"
            )
            user_features = try_load_user_features_from_vocal_profile(user_id)
            if user_features is None:
                raise RuntimeError(
                    "user_vocal_profiles 에 1차 추천용 컬럼(vocal_repr_embedding, f0_*, timbre_* 등)이 "
                    "없습니다. 보컬 분석 워커로 분석을 완료했는지, "
                    "sql/add_user_vocal_profiles_song_aligned_columns.sql 적용 여부를 확인하세요. "
                    "로컬/비상 시 FIRST_REC_FORCE_PIPELINE=1 과 s3_key 로 파이프라인 폴백 가능."
                )

        # Step 3: DB에서 song_features 조회
        print("\n[Step 3] DB에서 song_features 조회")
        song_features_list = get_all_song_features_from_db()
        
        if not song_features_list:
            raise RuntimeError("DB에 song_features가 없습니다.")
        
        # Step 4: 점수 계산
        print(f"\n[Step 4] 점수 계산 ({len(song_features_list)}개 곡)")
        results = []
        for i, song_features in enumerate(song_features_list, 1):
            song_id = song_features['song_id']
            if i % 100 == 0:
                print(f"  [{i}/{len(song_features_list)}] 진행 중...")
            
            try:
                score_result = score_song(user_features, song_features)
                results.append(score_result)
            except Exception as e:
                print(f"  ⚠️  {song_id} 점수 계산 실패: {e}")
                results.append({
                    'song_id': song_id,
                    'final_score': 0.0,
                    'error': str(e)
                })
        
        # Step 5: 정렬
        print("\n[Step 5] 결과 정렬")
        results_sorted = sorted(results, key=lambda x: x['final_score'], reverse=True)
        
        # Step 6: MongoDB에 basescore 저장 (상위 200개)
        print("\n[Step 6] MongoDB에 basescore 저장")
        save_basescore_to_mongodb(
            mongo_client,
            job_id,
            user_id,
            results_sorted,
            top_n=200
        )
        
        # Step 7: 상위 3곡을 recommendation_logs.first_recommended_songs 에 저장
        print("\n[Step 7] 1차 추천 Top3 저장 (상위 3곡)")
        top_3_songs = results_sorted[:3]
        first_recommendation = []
        for result in top_3_songs:
            song_id = result['song_id']
            song_info = get_song_info_from_db(supabase, song_id) or {}
            first_recommendation.append(
                {
                    'song_id': song_id,
                    'title': song_info.get('title', ''),
                    'artist': song_info.get('artist', ''),
                    'album_cover': song_info.get('album_cover'),
                    'score': result['final_score'],
                    'ecapa_score': result.get('ecapa_score', 0.0),
                    'pitch_total': result.get('pitch_total', result.get('pitch_score', 0.0)),
                    'timbre_score': result.get('timbre_score', 0.0),
                }
            )
        
        try:
            supabase.table("recommendation_logs").update({
                'first_recommended_songs': first_recommendation,
                'updated_at': datetime.now().isoformat()
            }).eq("id", job_id).execute()
            print(f"✓ first_recommended_songs 저장 완료: {len(first_recommendation)}개 곡")
        except Exception as e:
            print(f"⚠️  first_recommended_songs 저장 실패: {e}")
        
        # Status 업데이트: WAITING_FEEDBACK (2차 추천 시작 전에 잠시)
        update_recommendation_status(supabase, job_id, STATUS_WAITING_FEEDBACK)
        
        print("\n" + "="*70)
        print("✅ 1차 추천 완료")
        print("="*70)

        stage1_payload = {
            'total_songs': len(song_features_list),
            'top_200_saved': min(len(results_sorted), 200),
        }

        if not auto_run_stage2_after_stage1():
            print(
                "\n[INFO] 2차는 이 단계에서 실행하지 않습니다 (status=WAITING_FEEDBACK).\n"
                "      프론트→백으로 피드백을 반영한 뒤, SQS에 "
                '{"job_id","user_id","stage":"stage2"} 를 보내거나 2차 워커를 호출하세요.\n'
                "      통합 테스트로 1차 직후 2차까지 한 번에 돌리려면 RECOMMENDATION_AUTO_STAGE2=1"
            )
            return {
                'status': 'success',
                'job_id': job_id,
                'waiting_feedback': True,
                'stage1': stage1_payload,
            }

        print("\n" + "="*70)
        print("🔄 2차 추천 자동 실행 (RECOMMENDATION_AUTO_STAGE2=1)")
        print("="*70)

        try:
            from second_recommendation_worker import process_second_recommendation

            stage2_result = process_second_recommendation(job_id, user_id)

            if stage2_result.get('status') == 'success':
                print("\n" + "="*70)
                print("✅ 전체 추천 프로세스 완료 (1차 + 2차)")
                print("="*70)
                return {
                    'status': 'success',
                    'job_id': job_id,
                    'stage1': stage1_payload,
                    'stage2': stage2_result,
                }
            print(f"\n⚠️  2차 추천 실패: {stage2_result.get('error', 'Unknown error')}")
            return {
                'status': 'partial_success',
                'job_id': job_id,
                'stage1': stage1_payload,
                'stage2_error': stage2_result.get('error', 'Unknown error'),
            }
        except Exception as e:
            print(f"\n⚠️  2차 추천 실행 중 에러: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'partial_success',
                'job_id': job_id,
                'stage1': stage1_payload,
                'stage2_error': str(e),
            }

    except Exception as e:
        print(f"\n❌ 1차 추천 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        
        # Status 업데이트: FAILED
        update_recommendation_status(supabase, job_id, STATUS_FAILED, str(e))
        
        return {
            'status': 'failed',
            'job_id': job_id,
            'error': str(e)
        }
    finally:
        mongo_client.close()
        if temp_dir is not None and temp_dir.is_dir():
            shutil.rmtree(temp_dir, ignore_errors=True)


def get_feedback_from_db(supabase, job_id: str) -> Optional[Dict]:
    """
    recommendation_logs 테이블에서 피드백 조회
    
    Args:
        supabase: Supabase 클라이언트
        job_id: 작업 ID
    
    Returns:
        feedback: {
            'input_preferences': {...},
            'selected_genre': [...],
            'selected_keyword': [...]
        } 또는 None
    """
    try:
        res = (
            supabase.table("recommendation_logs")
            .select("input_preferences, selected_genre, selected_keyword")
            .eq("id", job_id)
            .execute()
        )
        
        if res.data and len(res.data) > 0:
            row = res.data[0]
            return {
                'input_preferences': row.get('input_preferences', {}),
                'selected_genre': row.get('selected_genre', []),
                'selected_keyword': row.get('selected_keyword', [])
            }
        return None
    except Exception as e:
        print(f"⚠️  피드백 조회 실패: {e}")
        return None


def adjust_basescore_with_feedback(
    mongo_client,
    job_id: str,
    input_preferences: Dict,
    basescore_multiplier: float = 1.2  # 피드백이 있는 곡의 가중치
) -> List[Dict]:
    """
    피드백 기반으로 MongoDB의 basescore 조정
    
    Args:
        mongo_client: MongoDB 클라이언트
        job_id: 작업 ID
        input_preferences: 유저 피드백 (좋아하는 곡 ID 리스트 등)
        basescore_multiplier: 피드백이 있는 곡의 가중치 배수
    
    Returns:
        adjusted_results: 조정된 결과 리스트
    """
    from pymongo import MongoClient
    
    db = mongo_client[MONGO_DB_NAME]
    collection = db["basescores"]
    
    # job_id로 basescore 조회
    basescores = list(collection.find({"job_id": job_id}).sort("basescore", -1))
    
    if not basescores:
        print("⚠️  basescore를 찾을 수 없습니다.")
        return []
    
    # input_preferences에서 좋아하는 곡 ID 추출
    # 예: input_preferences = {"liked_songs": ["song_id1", "song_id2"], ...}
    liked_song_ids = set()
    if isinstance(input_preferences, dict):
        # 다양한 키 형식 지원
        for key in ['liked_songs', 'preferred_songs', 'favorites', 'songs']:
            if key in input_preferences:
                songs = input_preferences[key]
                if isinstance(songs, list):
                    liked_song_ids.update(songs)
                break
    
    # basescore 조정
    adjusted_results = []
    for doc in basescores:
        song_id = doc.get('song_id')
        basescore = doc.get('basescore', 0.0)
        
        # 좋아하는 곡이면 가중치 적용
        if song_id in liked_song_ids:
            adjusted_score = basescore * basescore_multiplier
            print(f"  ✓ {song_id}: {basescore:.4f} → {adjusted_score:.4f} (가중치 적용)")
        else:
            adjusted_score = basescore
        
        # 결과 구성
        result = {
            'song_id': song_id,
            'basescore': basescore,
            'adjusted_score': adjusted_score,
            'title': doc.get('title', ''),
            'artist': doc.get('artist', ''),
            'genre': doc.get('genre', []),
            'keywords': doc.get('keywords', [])
        }
        adjusted_results.append(result)
    
    # adjusted_score 기준으로 재정렬
    adjusted_results.sort(key=lambda x: x['adjusted_score'], reverse=True)
    
    return adjusted_results


def save_recommend_songs_to_db(
    supabase,
    job_id: str,
    user_id: str,
    genre_results: Dict[str, List[Dict]]
) -> None:
    """
    장르별 추천 결과를 recommendation_logs에 저장
    
    Args:
        supabase: Supabase 클라이언트
        job_id: 작업 ID
        user_id: 유저 ID
        genre_results: {'발라드': [곡1, 곡2, ...], 'pop': [곡1, ...]}
    """
    # 2차 추천 결과 형식: JSON 객체
    recommend_songs = {}
    
    for genre, songs in genre_results.items():
        # 각 장르별로 최대 4곡만 저장
        recommend_songs[genre] = songs[:4]
    
    try:
        supabase.table("recommendation_logs").update({
            'recommend_songs': recommend_songs,
            'updated_at': datetime.now().isoformat()
        }).eq("id", job_id).execute()
        print(f"✓ recommend_songs 저장 완료: {len(genre_results)}개 장르")
    except Exception as e:
        # 구 스키마 호환: recommended_songs
        print(f"⚠️  recommend_songs 저장 실패, 구 컬럼으로 재시도: {e}")
        try:
            supabase.table("recommendation_logs").update({
                'recommended_songs': recommend_songs,
                'updated_at': datetime.now().isoformat()
            }).eq("id", job_id).execute()
            print(f"✓ recommended_songs 저장 완료: {len(genre_results)}개 장르")
        except Exception as e2:
            print(f"⚠️  2차 추천 결과 저장 실패(신/구 컬럼 모두): {e2}")


def process_stage2(
    job_id: str,
    user_id: str
) -> Dict:
    """
    2차 추천 처리 (RUNNING_STAGE2) — second_recommendation_worker에 위임.
    SQS body에 \"stage\": \"stage2\" 가 올 때 이 경로로 실행된다.
    """
    from second_recommendation_worker import process_second_recommendation

    return process_second_recommendation(job_id, user_id)


def process_recommendation_job(
    job_id: str,
    user_id: str,
    s3_key: str = "",
    stage: Optional[str] = None,
) -> Dict:
    """
    추천 작업 처리 (1차 또는 2차)

    Args:
        job_id: 작업 ID
        user_id: 유저 ID
        s3_key: stage1 기본 경로에서는 생략 가능 (user_vocal_profiles 사용).
            FIRST_REC_FORCE_PIPELINE=1 폴백 시에만 필요.
        stage: 처리할 단계 ('stage1' 또는 'stage2'), None이면 자동 판단

    Returns:
        result: 처리 결과
    """
    supabase = get_supabase_client()
    
    # 현재 상태 확인
    try:
        res = (
            supabase.table("recommendation_logs")
            .select("status")
            .eq("id", job_id)
            .execute()
        )
        
        if res.data and len(res.data) > 0:
            current_status = res.data[0].get('status')
        else:
            current_status = STATUS_QUEUED
    except Exception as e:
        print(f"⚠️  상태 조회 실패: {e}")
        current_status = STATUS_QUEUED
    
    # stage가 지정되지 않았으면 상태에 따라 자동 판단
    if stage is None:
        if current_status == STATUS_QUEUED or current_status == STATUS_RUNNING_STAGE1:
            stage = 'stage1'
        elif (
            current_status == STATUS_WAITING_FEEDBACK
            or current_status == STATUS_READY_FOR_STAGE2
            or current_status == STATUS_RUNNING_STAGE2
        ):
            stage = 'stage2'
        else:
            return {
                'status': 'skipped',
                'job_id': job_id,
                'reason': f'현재 상태: {current_status}'
            }
    
    # 단계별 처리
    if stage == 'stage1':
        return process_stage1(job_id, user_id, s3_key)
    elif stage == 'stage2':
        return process_stage2(job_id, user_id)
    else:
        return {
            'status': 'failed',
            'job_id': job_id,
            'error': f'알 수 없는 stage: {stage}'
        }


def receive_message_from_queue(sqs_client, queue_url: str) -> Optional[Dict]:
    """
    SQS Queue에서 메시지 수신
    
    Args:
        sqs_client: SQS 클라이언트
        queue_url: Queue URL
    
    Returns:
        message: {
            'job_id': ...,
            'user_id': ...,
            's3_key': ... (선택, 없으면 빈 문자열 — stage1 기본은 DB 프로필),
            'stage': ... (선택적)
        } 또는 None
    """
    try:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,  # Long polling
            VisibilityTimeout=300  # 5분
        )
        
        messages = response.get('Messages', [])
        if not messages:
            return None
        
        message = messages[0]
        body = json.loads(message['Body'])
        
        # SNS를 통한 전달인 경우
        if 'Message' in body:
            body = json.loads(body['Message'])
        
        return {
            'receipt_handle': message['ReceiptHandle'],
            'job_id': body.get('job_id'),
            'user_id': body.get('user_id'),
            's3_key': body.get('s3_key') or '',
            'stage': body.get('stage'),  # 선택적
        }
    except ClientError as e:
        print(f"⚠️  Queue 메시지 수신 실패: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️  메시지 파싱 실패: {e}")
        return None


def delete_message_from_queue(sqs_client, queue_url: str, receipt_handle: str) -> None:
    """SQS Queue에서 메시지 삭제"""
    try:
        sqs_client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        print("✓ Queue 메시지 삭제 완료")
    except ClientError as e:
        print(f"⚠️  Queue 메시지 삭제 실패: {e}")


def run_worker_once() -> None:
    """
    SQS에서 메시지 1건만 수신·처리·삭제 후 종료 (로컬에서 큐 연동 검증용).
    """
    if not SQS_QUEUE_URL:
        raise RuntimeError("SQS_QUEUE_URL이 .env에 설정되지 않았습니다.")

    sqs_client = boto3.client("sqs")
    print("\n" + "=" * 70)
    print("추천 워커 (1건 수신 모드)")
    print("=" * 70)
    print(f"  - Queue URL: {SQS_QUEUE_URL}")
    print("  - Long poll 최대 약 20초 대기")
    print("=" * 70 + "\n")

    message = receive_message_from_queue(sqs_client, SQS_QUEUE_URL)
    if not message:
        print("메시지 없음 (타임아웃). 큐에 메시지를 넣은 뒤 다시 실행하세요.")
        return

    job_id = message.get("job_id")
    user_id = message.get("user_id")
    s3_key = message.get("s3_key") or ""
    stage = message.get("stage")

    if not job_id or not user_id:
        print(f"⚠️  필수 필드 누락: job_id={job_id}, user_id={user_id}")
        delete_message_from_queue(sqs_client, SQS_QUEUE_URL, message["receipt_handle"])
        return

    print(f"\n📨 메시지 수신: job_id={job_id}, stage={stage or 'auto'}")
    result = process_recommendation_job(job_id, user_id, s3_key, stage)

    if result.get("status") == "success":
        print(f"✅ 작업 완료: {job_id}")
    elif result.get("status") == "partial_success":
        print(f"⚠️  부분 완료(1차 성공 등): {job_id}")
    elif result.get("status") == "skipped":
        print(f"⏭️  작업 스킵: {job_id} ({result.get('reason')})")
    else:
        print(f"❌ 작업 실패: {job_id} ({result.get('error')})")

    delete_message_from_queue(sqs_client, SQS_QUEUE_URL, message["receipt_handle"])


def run_worker_loop():
    """
    워커 메인 루프 (Queue에서 계속 메시지를 받아서 처리)
    """
    if not SQS_QUEUE_URL:
        raise RuntimeError("SQS_QUEUE_URL이 .env에 설정되지 않았습니다.")
    
    sqs_client = boto3.client('sqs')
    
    print("\n" + "="*70)
    print("🚀 추천 워커 시작")
    print("="*70)
    print(f"  - Queue URL: {SQS_QUEUE_URL}")
    print("="*70 + "\n")
    
    while True:
        try:
            # Queue에서 메시지 수신
            message = receive_message_from_queue(sqs_client, SQS_QUEUE_URL)
            
            if not message:
                print("대기 중... (메시지 없음)")
                time.sleep(5)
                continue
            
            job_id = message.get('job_id')
            user_id = message.get('user_id')
            s3_key = message.get('s3_key') or ''
            stage = message.get('stage')
            
            if not job_id or not user_id:
                print(f"⚠️  필수 필드 누락: job_id={job_id}, user_id={user_id}")
                delete_message_from_queue(sqs_client, SQS_QUEUE_URL, message['receipt_handle'])
                continue
            
            print(f"\n📨 메시지 수신: job_id={job_id}, stage={stage or 'auto'}")
            
            # 작업 처리
            result = process_recommendation_job(job_id, user_id, s3_key, stage)
            
            if result.get('status') == 'success':
                print(f"✅ 작업 완료: {job_id}")
            elif result.get('status') == 'skipped':
                print(f"⏭️  작업 스킵: {job_id} ({result.get('reason')})")
            else:
                print(f"❌ 작업 실패: {job_id} ({result.get('error')})")
            
            # 메시지 삭제
            delete_message_from_queue(sqs_client, SQS_QUEUE_URL, message['receipt_handle'])
            
        except KeyboardInterrupt:
            print("\n\n⚠️  워커 종료 요청")
            break
        except Exception as e:
            print(f"\n❌ 워커 에러: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(10)  # 에러 후 잠시 대기


# CLI 실행
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="추천 워커 (1차 + 2차 통합)"
    )
    parser.add_argument(
        "--job-id",
        type=str,
        help="작업 ID (직접 처리 모드)"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        help="유저 ID (직접 처리 모드)"
    )
    parser.add_argument(
        "--s3-key",
        type=str,
        default="",
        help="stage1 폴백용 S3 키 (FIRST_REC_FORCE_PIPELINE=1 일 때만 필요, 기본은 user_vocal_profiles)",
    )
    parser.add_argument(
        "--stage",
        type=str,
        choices=["stage1", "stage2"],
        help="처리할 단계 (기본값: 자동 판단)"
    )
    parser.add_argument(
        "--queue",
        action="store_true",
        help="Queue 모드 (메시지를 계속 받아서 처리)"
    )
    parser.add_argument(
        "--queue-once",
        action="store_true",
        help="SQS에서 1건만 받아 처리 후 종료 (로컬 Mongo·큐 연동 확인용)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.queue_once:
            run_worker_once()
        elif args.queue:
            # Queue 모드
            run_worker_loop()
        elif args.job_id and args.user_id:
            # 직접 처리 모드
            result = process_recommendation_job(
                job_id=args.job_id,
                user_id=args.user_id,
                s3_key=args.s3_key or "",
                stage=args.stage
            )
            
            if result.get('status') == 'success':
                print("\n✅ 작업 완료!")
                exit(0)
            else:
                print(f"\n❌ 작업 실패: {result.get('error', 'Unknown error')}")
                exit(1)
        else:
            print("❌ --queue / --queue-once 또는 --job-id/--user-id가 필요합니다.")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


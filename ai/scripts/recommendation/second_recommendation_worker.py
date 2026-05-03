"""
2차 추천 워커

유저의 피드백과 위시리스트 등을 분석해서 재정렬:
- 유저의 재랭킹 (top3)
- 유저의 위시리스트
- 유저의 선호 가수
- 유저의 차단 곡, 차단 가수

비슷함 정의: song_repr_embedding (ECAPA 톤 임베딩) 기반 cosine similarity
"""
import json
import os
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
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
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "singchronize")

# Status 상수
STATUS_RUNNING_STAGE2 = "RUNNING_STAGE2"
STATUS_DONE = "DONE"
STATUS_FAILED = "FAILED"

# 장르 및 상황 카테고리
GENRE_KEYS = ['POP', 'ROCK', 'R&B', 'TROT', 'BALLAD', 'DANCE', 'ALL']  # 7개 (ALL 포함)

# UI 표시용 canonical 상황 문구 (8개)
SITUATION_KEYS = [
    "회식하며 즐길 때",
    "가족과 함께할 때",
    "친구랑 놀 때",
    "연인과 함께할 때",
    "공연을 준비할 때",
    "신나게 놀고 싶을 때",
    "감성에 젖고 싶을 때",
    "엔딩곡이 필요할 때",
]  # 8개

# 과거/호환 alias -> canonical 매핑
SITUATION_ALIAS_TO_CANONICAL = {
    "회식": "회식하며 즐길 때",
    "가족": "가족과 함께할 때",
    "친구": "친구랑 놀 때",
    "연인": "연인과 함께할 때",
    "공연": "공연을 준비할 때",
    "신남": "신나게 놀고 싶을 때",
    "감성": "감성에 젖고 싶을 때",
    "엔딩": "엔딩곡이 필요할 때",
    # canonical 자체도 통과
    "회식하며 즐길 때": "회식하며 즐길 때",
    "가족과 함께할 때": "가족과 함께할 때",
    "친구랑 놀 때": "친구랑 놀 때",
    "연인과 함께할 때": "연인과 함께할 때",
    "공연을 준비할 때": "공연을 준비할 때",
    "신나게 놀고 싶을 때": "신나게 놀고 싶을 때",
    "감성에 젖고 싶을 때": "감성에 젖고 싶을 때",
    "엔딩곡이 필요할 때": "엔딩곡이 필요할 때",
}

# songs.genre(한글/복합 표기) <-> 프론트 선택값(영문 enum) 정규화 매핑
GENRE_ALIAS_TO_KEY = {
    # canonical
    "POP": "POP",
    "ROCK": "ROCK",
    "R&B": "R&B",
    "RNB": "R&B",
    "TROT": "TROT",
    "BALLAD": "BALLAD",
    "DANCE": "DANCE",
    "ALL": "ALL",
    # KR labels
    "발라드": "BALLAD",
    "댄스": "DANCE",
    "트로트": "TROT",
    "락": "ROCK",
    "락/메탈": "ROCK",
    "록": "ROCK",
    "록/메탈": "ROCK",
    "메탈": "ROCK",
    "R&B/어반": "R&B",
    "알앤비": "R&B",
    "알앤비/어반": "R&B",
    "어반": "R&B",
    "팝": "POP",
    "전체": "ALL",
}

# 결과 JSON에 저장할 장르 라벨 및 기본 정렬 순서
GENRE_KEY_TO_LABEL = {
    "ALL": "전체",
    "BALLAD": "발라드",
    "POP": "POP",
    "DANCE": "댄스",
    "R&B": "R&B",
    "ROCK": "락/메탈",
    "TROT": "트로트",
}
GENRE_OUTPUT_ORDER = ["ALL", "BALLAD", "POP", "DANCE", "R&B", "ROCK", "TROT"]


def normalize_genre_key(raw: Optional[str]) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    s = raw.strip()
    if not s:
        return None
    su = s.upper()
    if su in GENRE_ALIAS_TO_KEY:
        return GENRE_ALIAS_TO_KEY[su]
    if s in GENRE_ALIAS_TO_KEY:
        return GENRE_ALIAS_TO_KEY[s]
    return None

# 2차 추천 파라미터
BASE_SCORE_WEIGHT = 0.75
PREFERENCE_SCORE_WEIGHT = 0.25
TOP1_SIM_WEIGHT = 0.65
TOP2_SIM_WEIGHT = 0.20
TOP3_SIM_WEIGHT = 0.05
WISHLIST_SIM_WEIGHT = 0.10
BONUS_WISH = 0.25  # 위시리스트 보너스
BONUS_ARTIST = 0.07  # 선호 가수 보너스
BLOCK_THRESHOLD = 0.80  # 차단 곡 유사도 임계값
BLOCK_PENALTY_MU = 0.25  # 차단 페널티 배수
BLOCK_EXCLUDE_THRESHOLD = 0.92  # 차단 곡 제외 임계값 (옵션)


def get_supabase_client():
    """Supabase 클라이언트 생성"""
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL이 .env에 설정되지 않았습니다.")
    
    if not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY가 .env에 설정되지 않았습니다.")
    
    from supabase import create_client, Client
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"✓ Supabase 클라이언트 생성 성공")
        return client
    except Exception as e:
        raise RuntimeError(f"Supabase 클라이언트 생성 실패: {e}") from e


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
    """recommendation_logs 테이블의 status 업데이트"""
    update_data = {
        'status': status,
        'updated_at': datetime.now().isoformat()
    }
    
    if status == STATUS_RUNNING_STAGE2:
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


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity 계산"""
    a_norm = a / (np.linalg.norm(a) + 1e-8)
    b_norm = b / (np.linalg.norm(b) + 1e-8)
    return float(np.dot(a_norm, b_norm))


def get_song_embedding_from_db(supabase, song_id: str) -> Optional[np.ndarray]:
    """
    song_features 테이블에서 곡의 ECAPA 임베딩 조회 (단일 곡)
    
    ⚠️  배치 조회가 필요하면 get_song_embeddings_batch 사용 권장
    
    Args:
        supabase: Supabase 클라이언트
        song_id: 곡 ID
    
    Returns:
        embedding: 192차원 numpy array 또는 None
    """
    try:
        res = (
            supabase.table("song_features")
            .select("song_repr_embedding")
            .eq("song_id", song_id)
            .execute()
        )
        
        if res.data and len(res.data) > 0:
            embedding = res.data[0].get('song_repr_embedding')
            
            # vector 타입을 numpy array로 변환
            if isinstance(embedding, str):
                embedding = embedding.strip('[]').split(',')
                embedding = [float(x.strip()) for x in embedding]
            elif isinstance(embedding, list):
                embedding = [float(x) for x in embedding]
            
            return np.array(embedding)
        return None
    except Exception as e:
        print(f"⚠️  임베딩 조회 실패 (song_id={song_id}): {e}")
        return None


def get_song_embeddings_batch(supabase, song_ids: List[str]) -> Dict[str, np.ndarray]:
    """
    song_features 테이블에서 여러 곡의 ECAPA 임베딩을 한 번에 조회 (배치 조회)
    
    Args:
        supabase: Supabase 클라이언트
        song_ids: 곡 ID 리스트
    
    Returns:
        embeddings_dict: {song_id: embedding_array, ...}
    """
    if not song_ids:
        return {}
    
    try:
        # Supabase의 in_ 쿼리로 한 번에 조회
        res = (
            supabase.table("song_features")
            .select("song_id, song_repr_embedding")
            .in_("song_id", song_ids)
            .execute()
        )
        
        embeddings_dict = {}
        for row in (res.data or []):
            song_id = row.get('song_id')
            embedding = row.get('song_repr_embedding')
            
            if embedding is None:
                continue
            
            # vector 타입을 numpy array로 변환
            if isinstance(embedding, str):
                embedding = embedding.strip('[]').split(',')
                embedding = [float(x.strip()) for x in embedding]
            elif isinstance(embedding, list):
                embedding = [float(x) for x in embedding]
            
            embeddings_dict[song_id] = np.array(embedding)
        
        print(f"  ✓ 배치 임베딩 조회: {len(embeddings_dict)}/{len(song_ids)}개 성공")
        return embeddings_dict
        
    except Exception as e:
        print(f"⚠️  배치 임베딩 조회 실패: {e}")
        return {}


def get_song_metadata_from_db(supabase, song_id: str) -> Optional[Dict]:
    """
    songs 테이블에서 곡 메타데이터 조회 (단일 곡)
    
    ⚠️  배치 조회가 필요하면 get_song_metadata_batch 사용 권장
    
    Returns:
        metadata: {
            'id', 'title', 'artist', 'album_cover', 'bpm', 'key', 'genre', 'tags', 'situations' (선택적)
        } 또는 None
    """
    try:
        res = (
            supabase.table("songs")
            .select("id, title, artist, album_cover, bpm, key, genre, tags")
            .eq("id", song_id)
            .execute()
        )
        
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception as e:
        print(f"⚠️  곡 메타데이터 조회 실패 (song_id={song_id}): {e}")
        return None


def get_song_metadata_batch(supabase, song_ids: List[str]) -> Dict[str, Dict]:
    """
    songs 테이블에서 여러 곡의 메타데이터를 한 번에 조회 (배치 조회)
    
    Args:
        supabase: Supabase 클라이언트
        song_ids: 곡 ID 리스트
    
    Returns:
        metadata_dict: {song_id: {id, title, artist, album_cover, bpm, key, genre, tags}, ...}
    """
    if not song_ids:
        return {}
    
    try:
        # Supabase의 in_ 쿼리로 한 번에 조회
        res = (
            supabase.table("songs")
            .select("id, title, artist, album_cover, bpm, key, genre, tags")
            .in_("id", song_ids)
            .execute()
        )
        
        metadata_dict = {}
        for row in (res.data or []):
            song_id = row.get('id')
            if song_id:
                metadata_dict[song_id] = row
        
        print(f"  ✓ 배치 메타데이터 조회: {len(metadata_dict)}/{len(song_ids)}개 성공")
        return metadata_dict
        
    except Exception as e:
        print(f"⚠️  배치 메타데이터 조회 실패: {e}")
        return {}


def get_artist_id_from_song(supabase, song_id: str) -> Optional[str]:
    """
    곡 ID로부터 가수 ID 조회 (songs 테이블의 artist 필드 사용)
    
    Note: 현재는 artist가 문자열이므로, artist 이름을 그대로 반환합니다.
    향후 artist_id 컬럼이 추가되면 수정 필요.
    """
    metadata = get_song_metadata_from_db(supabase, song_id)
    if metadata:
        return metadata.get('artist')  # 또는 metadata.get('artist_id')
    return None


def get_basescores_from_mongodb(mongo_client, job_id: str, limit: int = 400) -> List[Dict]:
    """
    MongoDB에서 basescore 조회 (상위 N개)
    
    Args:
        mongo_client: MongoDB 클라이언트
        job_id: 작업 ID
        limit: 가져올 최대 개수
    
    Returns:
        basescores: [{song_id, basescore, genre, keywords, ...}, ...]
    """
    from pymongo import MongoClient
    
    db = mongo_client[MONGO_DB_NAME]
    collection = db["basescores"]
    
    basescores = list(
        collection.find({"job_id": job_id})
        .sort("basescore", -1)
        .limit(limit)
    )
    
    print(f"✓ MongoDB에서 {len(basescores)}개 basescore 조회")
    return basescores


def get_user_feedback_from_db(supabase, job_id: str) -> Dict:
    """
    recommendation_logs 테이블에서 유저 피드백 조회
    
    Returns:
        feedback: {
            # 1차 추천에 대한 재랭킹 결과 (유저가 고른 1~3등)
            'reranking_top3': [song_id1, song_id2, song_id3],
            # 선택된 장르/상황 (없으면 기본 전체)
            'selected_genres': ['POP', ...],
            'selected_situations': ['감성에 젖고 싶을 때', ...],
            
            # TODO: 아래 값들은 별도 테이블에서 읽어오도록 확장 예정
            # 현재는 input_preferences에서는 **절대** 읽지 않고, 빈 리스트로 유지한다.
            'wishlist': [],           # 위시리스트 곡 ID 리스트
            'preferred_artists': [],  # 선호 가수 이름 리스트
            'blocked_songs': [],      # 차단 곡 ID 리스트
            'blocked_artists': []     # 차단 가수 이름 리스트
        }
    """
    try:
        # 1) recommendation_logs에서 job 정보 + 재랭킹 정보 조회
        res = (
            supabase.table("recommendation_logs")
            .select("user_id, input_preferences, selected_genre, selected_keyword")
            .eq("id", job_id)
            .execute()
        )
        
        if not res.data:
            return {
                'reranking_top3': [],
                'wishlist': [],
                'preferred_artists': [],
                'blocked_songs': [],
                'blocked_artists': [],
                'selected_genres': [],
                'selected_situations': [],
            }
        
        row = res.data[0]
        user_id = row.get('user_id')
        input_preferences = row.get('input_preferences', {})
        
        # 기본 피드백 구조
        feedback = {
            'reranking_top3': [],
            'wishlist': [],
            'preferred_artists': [],
            'blocked_songs': [],
            'blocked_artists': [],
            'selected_genres': [],
            'selected_situations': [],
        }

        # 1-0) 선택 장르/상황 조회 (선택된 것만 결과에 담기 위함)
        raw_selected_genres = row.get('selected_genre', [])
        if isinstance(raw_selected_genres, str):
            raw_selected_genres = [raw_selected_genres]
        if isinstance(raw_selected_genres, list):
            genres_norm = []
            for g in raw_selected_genres:
                if not isinstance(g, str):
                    continue
                nk = normalize_genre_key(g)
                if nk in GENRE_KEYS:
                    genres_norm.append(nk)
            # 중복 제거 (순서 유지)
            feedback['selected_genres'] = list(dict.fromkeys(genres_norm))

        raw_selected_keywords = row.get('selected_keyword', [])
        if isinstance(raw_selected_keywords, str):
            raw_selected_keywords = [raw_selected_keywords]
        if isinstance(raw_selected_keywords, list):
            situations_norm = []
            for s in raw_selected_keywords:
                if not isinstance(s, str):
                    continue
                canonical = SITUATION_ALIAS_TO_CANONICAL.get(s.strip())
                if canonical:
                    situations_norm.append(canonical)
            feedback['selected_situations'] = list(dict.fromkeys(situations_norm))
        
        # 1-1) input_preferences에서는 **재랭킹 정보(reranking_top3)만** 사용
        if isinstance(input_preferences, dict):
            reranking_top3 = input_preferences.get('reranking_top3', [])
            # 형식 보정: 단일 문자열이 올 수도 있으므로 리스트로 강제
            if isinstance(reranking_top3, str):
                feedback['reranking_top3'] = [reranking_top3]
            elif isinstance(reranking_top3, list):
                feedback['reranking_top3'] = [
                    sid for sid in reranking_top3 if isinstance(sid, str)
                ]
        
        # user_id가 없으면 여기서 끝
        if not user_id:
            return feedback
        
        # 2) wishlist_items 테이블에서 위시 곡 조회
        try:
            wish_res = (
                supabase.table("wishlist_items")
                .select("song_id")
                .eq("user_id", user_id)
                .execute()
            )
            wish_rows = wish_res.data or []
            feedback['wishlist'] = [row['song_id'] for row in wish_rows if row.get('song_id')]
            print(f"  ✓ wishlist_items에서 위시 곡 {len(feedback['wishlist'])}개 조회")
        except Exception as e:
            print(f"⚠️  wishlist_items 조회 실패: {e}")
        
        # 3) blocked_songs 테이블에서 차단 곡 조회
        try:
            blocked_res = (
                supabase.table("blocked_songs")
                .select("song_id")
                .eq("user_id", user_id)
                .execute()
            )
            blocked_rows = blocked_res.data or []
            feedback['blocked_songs'] = [
                row['song_id'] for row in blocked_rows if row.get('song_id')
            ]
            print(f"  ✓ blocked_songs에서 차단 곡 {len(feedback['blocked_songs'])}개 조회")
        except Exception as e:
            print(f"⚠️  blocked_songs 조회 실패: {e}")
        
        # 4) artist_user_actions 테이블에서 선호/차단 가수 조회
        try:
            artist_res = (
                supabase.table("artist_user_actions")
                .select("artist_name, action")
                .eq("user_id", user_id)
                .execute()
            )
            artist_rows = artist_res.data or []
            preferred_artists = []
            blocked_artists = []
            for a in artist_rows:
                name = a.get('artist_name')
                action = str(a.get('action') or '').upper()
                if not name:
                    continue
                if action == 'PREFER':
                    preferred_artists.append(name)
                elif action == 'BLOCK':
                    blocked_artists.append(name)
            feedback['preferred_artists'] = preferred_artists
            feedback['blocked_artists'] = blocked_artists
            print(
                f"  ✓ artist_user_actions에서 선호 {len(preferred_artists)}명, "
                f"차단 {len(blocked_artists)}명 조회"
            )
        except Exception as e:
            print(f"⚠️  artist_user_actions 조회 실패: {e}")
        
        return feedback
    
    except Exception as e:
        print(f"⚠️  피드백 조회 실패: {e}")
        return {
            'reranking_top3': [],
            'wishlist': [],
            'preferred_artists': [],
            'blocked_songs': [],
            'blocked_artists': [],
            'selected_genres': [],
            'selected_situations': [],
        }


def create_preference_vector(
    supabase,
    reranking_top3: List[str],
    wishlist: List[str]
) -> Optional[np.ndarray]:
    """
    유저 취향 벡터 생성 (단일 조회 버전 - 레거시 호환용)
    
    ⚠️  배치 조회가 가능하면 create_preference_vectors_from_cache 사용 권장
    
    Args:
        supabase: Supabase 클라이언트
        reranking_top3: 재랭킹 상위 3곡 ID 리스트
        wishlist: 위시리스트 곡 ID 리스트
    
    Returns:
        pref_vec: 192차원 numpy array (정규화됨) 또는 None
    """
    session_pref = None
    wish_pref = None
    
    # 세션 취향 (재랭킹 top3)
    if reranking_top3:
        embeddings = []
        weights = [1.0, 0.6, 0.3]  # 가중치
        
        for i, song_id in enumerate(reranking_top3[:3]):
            emb = get_song_embedding_from_db(supabase, song_id)
            if emb is not None:
                embeddings.append(emb * weights[i])
        
        if embeddings:
            session_pref = np.sum(embeddings, axis=0)
            session_pref = session_pref / (np.linalg.norm(session_pref) + 1e-8)
            print(f"  ✓ 세션 취향 벡터 생성: {len(embeddings)}개 곡")
    
    # 위시 취향
    if wishlist:
        embeddings = []
        for song_id in wishlist:
            emb = get_song_embedding_from_db(supabase, song_id)
            if emb is not None:
                embeddings.append(emb)
        
        if embeddings:
            wish_pref = np.mean(embeddings, axis=0)
            wish_pref = wish_pref / (np.linalg.norm(wish_pref) + 1e-8)
            print(f"  ✓ 위시 취향 벡터 생성: {len(embeddings)}개 곡")
    
    # 최종 취향 벡터
    if session_pref is not None and wish_pref is not None:
        pref_vec = 0.8 * session_pref + 0.2 * wish_pref
        pref_vec = pref_vec / (np.linalg.norm(pref_vec) + 1e-8)
        print(f"  ✓ 최종 취향 벡터 생성 (세션 0.8 + 위시 0.2)")
    elif session_pref is not None:
        pref_vec = session_pref
        print(f"  ✓ 최종 취향 벡터 생성 (세션만)")
    elif wish_pref is not None:
        pref_vec = wish_pref
        print(f"  ✓ 최종 취향 벡터 생성 (위시만)")
    else:
        pref_vec = None
        print(f"  ⚠️  취향 벡터를 생성할 수 없습니다.")
    
    return pref_vec


def create_preference_vectors_from_cache(
    song_embeddings: Dict[str, np.ndarray],
    reranking_top3: List[str],
    wishlist: List[str]
) -> Tuple[List[Optional[np.ndarray]], Optional[np.ndarray]]:
    """
    유저 취향 벡터 생성 (배치 조회된 임베딩 캐시 사용)
    
    Args:
        song_embeddings: {song_id: embedding_array, ...} 딕셔너리
        reranking_top3: 재랭킹 상위 3곡 ID 리스트
        wishlist: 위시리스트 곡 ID 리스트
    
    Returns:
        (top_vectors, wish_center_vec):
            - top_vectors: [top1_vec, top2_vec, top3_vec] (없으면 None)
            - wish_center_vec: wishlist 평균 벡터 (없으면 None)
    """
    top_vectors: List[Optional[np.ndarray]] = [None, None, None]
    top_count = 0
    for i, song_id in enumerate(reranking_top3[:3]):
        emb = song_embeddings.get(song_id)
        if emb is not None:
            top_vectors[i] = emb / (np.linalg.norm(emb) + 1e-8)
            top_count += 1
    if top_count > 0:
        print(f"  ✓ 재랭킹 기준 벡터 준비: {top_count}/3개")

    wish_center_vec = None
    if wishlist:
        embeddings = []
        for song_id in wishlist:
            emb = song_embeddings.get(song_id)
            if emb is not None:
                embeddings.append(emb)
        
        if embeddings:
            wish_center_vec = np.mean(embeddings, axis=0)
            wish_center_vec = wish_center_vec / (np.linalg.norm(wish_center_vec) + 1e-8)
            print(f"  ✓ 위시 취향 벡터 생성: {len(embeddings)}개 곡")
    
    if top_count == 0 and wish_center_vec is None:
        print(f"  ⚠️  취향 벡터를 생성할 수 없습니다.")
    else:
        wish_flag = "있음" if wish_center_vec is not None else "없음"
        print(f"  ✓ 취향 벡터 준비 완료 (재랭킹: {top_count}/3, 위시: {wish_flag})")

    return top_vectors, wish_center_vec


def calculate_block_penalty(
    song_embedding: np.ndarray,
    blocked_embeddings: Dict[str, np.ndarray]
) -> float:
    """
    차단 곡과의 유사도 기반 페널티 계산 (배치 조회된 임베딩 캐시 사용)
    
    Args:
        song_embedding: 후보 곡의 임베딩
        blocked_embeddings: {blocked_song_id: embedding_array, ...} 딕셔너리
    
    Returns:
        penalty: 페널티 점수 (0 이상)
    """
    if not blocked_embeddings:
        return 0.0
    
    max_sim = 0.0
    for blocked_song_id, blocked_emb in blocked_embeddings.items():
        sim = cosine_similarity(song_embedding, blocked_emb)
        max_sim = max(max_sim, sim)
    
    # 임계값 이상이면 페널티 적용
    if max_sim >= BLOCK_THRESHOLD:
        penalty = BLOCK_PENALTY_MU * max(0, max_sim - BLOCK_THRESHOLD)
        return penalty
    
    return 0.0


def calculate_score2(
    base_score: float,
    top_vectors: List[Optional[np.ndarray]],
    wish_center_vec: Optional[np.ndarray],
    song_embedding: np.ndarray,
    song_id: str,
    artist: str,
    feedback: Dict,
    blocked_embeddings: Dict[str, np.ndarray]
) -> Tuple[float, Dict]:
    """
    2차 점수 계산
    
    Args:
        base_score: 1차 추천 basescore
        top_vectors: [top1_vec, top2_vec, top3_vec]
        wish_center_vec: wishlist 평균 벡터
        song_embedding: 곡 임베딩
        song_id: 곡 ID
        artist: 가수 이름
        feedback: 유저 피드백
        blocked_embeddings: 차단 곡 임베딩 캐시 {song_id: embedding, ...}
    
    Returns:
        (score2, details): (2차 점수, 상세 정보)
    """
    details = {
        'base_score': base_score,
        'pref_score': 0.0,
        'pref_score_feedback': 0.0,
        'pref_score_wishlist': 0.0,
        'sim_top1': 0.0,
        'sim_top2': 0.0,
        'sim_top3': 0.0,
        'sim_wishlist_center': 0.0,
        'bonus_wish': 0.0,
        'bonus_artist': 0.0,
        'penalty': 0.0
    }
    
    # 1. 취향 점수 (피드백/위시 분리)
    top1_vec = top_vectors[0] if len(top_vectors) > 0 else None
    top2_vec = top_vectors[1] if len(top_vectors) > 1 else None
    top3_vec = top_vectors[2] if len(top_vectors) > 2 else None

    sim_top1 = cosine_similarity(song_embedding, top1_vec) if top1_vec is not None else 0.0
    sim_top2 = cosine_similarity(song_embedding, top2_vec) if top2_vec is not None else 0.0
    sim_top3 = cosine_similarity(song_embedding, top3_vec) if top3_vec is not None else 0.0
    sim_wishlist_center = (
        cosine_similarity(song_embedding, wish_center_vec)
        if wish_center_vec is not None
        else 0.0
    )

    pref_score_feedback = (
        TOP1_SIM_WEIGHT * sim_top1 +
        TOP2_SIM_WEIGHT * sim_top2 +
        TOP3_SIM_WEIGHT * sim_top3
    )
    pref_score_wishlist = WISHLIST_SIM_WEIGHT * sim_wishlist_center
    pref_score = pref_score_feedback + pref_score_wishlist

    details['sim_top1'] = sim_top1
    details['sim_top2'] = sim_top2
    details['sim_top3'] = sim_top3
    details['sim_wishlist_center'] = sim_wishlist_center
    details['pref_score_feedback'] = pref_score_feedback
    details['pref_score_wishlist'] = pref_score_wishlist
    details['pref_score'] = pref_score
    
    # 2. 위시리스트 보너스
    if song_id in feedback.get('wishlist', []):
        details['bonus_wish'] = BONUS_WISH
    
    # 3. 선호 가수 보너스
    if artist in feedback.get('preferred_artists', []):
        details['bonus_artist'] = BONUS_ARTIST
    
    # 4. 차단 페널티 (캐시 사용)
    penalty = calculate_block_penalty(song_embedding, blocked_embeddings)
    details['penalty'] = penalty
    
    # 최종 점수
    score2 = (
        BASE_SCORE_WEIGHT * base_score +
        PREFERENCE_SCORE_WEIGHT * pref_score +
        details['bonus_wish'] +
        details['bonus_artist'] -
        penalty
    )
    
    return score2, details


def parse_genres(genre_str: Optional[str]) -> List[str]:
    """
    songs.genre → 장르별 버킷용 키 리스트.

    DB에 '전체'·ALL 등이 들어 있어도 실제 장르가 아니므로 제외한다.
    출력의 "전체" 구간은 항상 scored 전체 정렬 상위 4곡으로만 채운다.
    """
    if not genre_str:
        return []
    
    if isinstance(genre_str, list):
        raw_genres = [g.strip() for g in genre_str if isinstance(g, str) and g.strip()]
    elif isinstance(genre_str, str):
        raw_genres = [g.strip() for g in genre_str.split(',') if g.strip()]
    else:
        return []
    
    normalized = []
    for g in raw_genres:
        nk = normalize_genre_key(g)
        if nk and nk != "ALL":
            normalized.append(nk)

    # 중복 제거 (순서 유지)
    return list(dict.fromkeys(normalized))


def parse_situations(tags_str: Optional[str]) -> List[str]:
    """
    tags 필드에서 상황(situation) 추출

    DB에 jsonb 형태로 저장된 경우 (예: {"situationLabel": "감성에 젖고 싶을 때"} 형태)도 지원한다.
    """
    if tags_str is None or tags_str == "":
        return []

    if isinstance(tags_str, str):
        # json 문자열일 수 있어 파싱 시도
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

    situations: List[str] = []
    for item in tags:
        label: Optional[str] = None
        if isinstance(item, dict):
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


def process_second_recommendation(job_id: str, user_id: str) -> Dict:
    """
    2차 추천 처리 메인 함수
    
    Args:
        job_id: 작업 ID
        user_id: 유저 ID
    
    Returns:
        result: 처리 결과
    """
    print("\n" + "="*70)
    print(f"🎯 2차 추천 처리 시작")
    print("="*70)
    print(f"  - job_id: {job_id}")
    print(f"  - user_id: {user_id}")
    print("="*70)
    
    supabase = get_supabase_client()
    mongo_client = get_mongo_client()
    
    # Status 업데이트: RUNNING_STAGE2
    update_recommendation_status(supabase, job_id, STATUS_RUNNING_STAGE2)
    
    try:
        # Step 1: 유저 피드백 조회
        print("\n[Step 1] 유저 피드백 조회")
        feedback = get_user_feedback_from_db(supabase, job_id)
        print(f"  - 재랭킹 top3: {len(feedback['reranking_top3'])}개")
        print(f"  - 위시리스트: {len(feedback['wishlist'])}개")
        print(f"  - 선호 가수: {len(feedback['preferred_artists'])}개")
        print(f"  - 차단 곡: {len(feedback['blocked_songs'])}개")
        print(f"  - 차단 가수: {len(feedback['blocked_artists'])}개")
        print(f"  - 선택 장르: {len(feedback.get('selected_genres', []))}개")
        print(f"  - 선택 상황: {len(feedback.get('selected_situations', []))}개")
        
        # Step 2: MongoDB에서 basescore 조회 (최대 400개)
        print("\n[Step 2] MongoDB에서 basescore 조회")
        basescores = get_basescores_from_mongodb(mongo_client, job_id, limit=400)
        
        if not basescores:
            raise RuntimeError("basescore를 찾을 수 없습니다.")
        
        # Step 3: 하드 필터 (차단 곡/가수 제거)
        print("\n[Step 3] 하드 필터 적용")
        blocked_songs = set(feedback.get('blocked_songs', []))
        blocked_artists = set(feedback.get('blocked_artists', []))
        
        filtered_basescores = []
        excluded_count = 0
        
        for doc in basescores:
            song_id = doc.get('song_id')
            artist = doc.get('artist', '')
            
            # 차단 곡/가수 제거
            if song_id in blocked_songs:
                excluded_count += 1
                continue
            
            if artist in blocked_artists:
                excluded_count += 1
                continue
            
            filtered_basescores.append(doc)
        
        print(f"  ✓ {excluded_count}개 곡 제외, {len(filtered_basescores)}개 곡 남음")
        
        # Step 4: 배치 조회 준비 (모든 필요한 song_id 수집)
        print("\n[Step 4] 배치 조회 준비")
        all_song_ids = [doc.get('song_id') for doc in filtered_basescores]
        blocked_song_ids = feedback.get('blocked_songs', [])
        reranking_song_ids = feedback.get('reranking_top3', [])
        wishlist_song_ids = feedback.get('wishlist', [])
        
        # 모든 필요한 song_id 수집 (후보 곡 + 차단 곡 + 재랭킹 곡 + 위시리스트 곡)
        all_needed_song_ids = list(set(
            all_song_ids + 
            blocked_song_ids + 
            reranking_song_ids + 
            wishlist_song_ids
        ))
        print(f"  - 조회할 곡 수: {len(all_needed_song_ids)}개")
        print(f"    (후보 {len(all_song_ids)}개 + 차단 {len(blocked_song_ids)}개 + 재랭킹 {len(reranking_song_ids)}개 + 위시 {len(wishlist_song_ids)}개)")
        
        # 배치 조회: 임베딩과 메타데이터를 한 번에 가져오기
        print("\n[Step 4.1] 배치 조회 실행")
        song_embeddings = get_song_embeddings_batch(supabase, all_needed_song_ids)
        song_metadata = get_song_metadata_batch(supabase, all_needed_song_ids)
        
        # Step 4.2: 취향 벡터 생성 (이제 캐시에서 가져오기)
        print("\n[Step 4.2] 취향 벡터 생성")
        top_vectors, wish_center_vec = create_preference_vectors_from_cache(
            song_embeddings,
            reranking_song_ids,
            wishlist_song_ids
        )
        
        # 차단 곡 임베딩도 미리 준비
        blocked_embeddings = {}
        for blocked_song_id in blocked_song_ids:
            if blocked_song_id in song_embeddings:
                blocked_embeddings[blocked_song_id] = song_embeddings[blocked_song_id]
        
        print(f"  ✓ 임베딩 캐시: {len(song_embeddings)}개")
        print(f"  ✓ 메타데이터 캐시: {len(song_metadata)}개")
        print(f"  ✓ 차단 곡 임베딩: {len(blocked_embeddings)}개")
        
        # Step 5: 곡별 2차 점수 계산 (이제 딕셔너리에서 가져오기만 함)
        print(f"\n[Step 5] 2차 점수 계산 ({len(filtered_basescores)}개 곡)")
        scored_songs = []
        
        for doc in filtered_basescores:
            song_id = doc.get('song_id')
            base_score = doc.get('basescore', 0.0)
            artist = doc.get('artist', '')
            
            # 캐시에서 임베딩 가져오기 (쿼리 없음!)
            song_embedding = song_embeddings.get(song_id)
            if song_embedding is None:
                print(f"  ⚠️  임베딩 없음: {song_id}")
                continue
            
            # 차단 곡과의 유사도 확인 (제외 여부 결정) - 캐시에서 가져오기
            if blocked_embeddings:
                max_block_sim = 0.0
                for blocked_song_id, blocked_emb in blocked_embeddings.items():
                    sim = cosine_similarity(song_embedding, blocked_emb)
                    max_block_sim = max(max_block_sim, sim)
                
                # 매우 유사한 차단 곡은 제외
                if max_block_sim >= BLOCK_EXCLUDE_THRESHOLD:
                    continue
            
            # 2차 점수 계산
            score2, details = calculate_score2(
                base_score,
                top_vectors,
                wish_center_vec,
                song_embedding,
                song_id,
                artist,
                feedback,
                blocked_embeddings
            )
            
            # 캐시에서 메타데이터 가져오기 (쿼리 없음!)
            metadata = song_metadata.get(song_id, {})
            genres = parse_genres(metadata.get('genre') if metadata else None)
            situations = parse_situations(metadata.get('tags') if metadata else None)
            
            scored_songs.append({
                'song_id': song_id,
                'title': doc.get('title', '') or metadata.get('title', ''),
                'artist': artist or metadata.get('artist', ''),
                'album_cover': metadata.get('album_cover'),
                'bpm': metadata.get('bpm'),
                'key': metadata.get('key'),
                'score2': score2,
                'base_score': base_score,
                'genres': genres,
                'situations': situations,
                'details': details
            })
        
        print(f"  ✓ {len(scored_songs)}개 곡 점수 계산 완료")
        
        # Step 6: 멀티 태그 그룹별 top4 뽑기
        print("\n[Step 6] 장르별/상황별 top4 추출")
        
        # "전체": DB 장르가 아님 — 후보 전체를 score2 기준 정렬한 뒤 상위 4곡만 사용
        all_songs_sorted = sorted(scored_songs, key=lambda x: x['score2'], reverse=True)
        
        # 장르별 결과: 유저 선택값만 반영하되, ALL(전체)은 항상 첫 번째로 포함
        raw_selected_genres = feedback.get('selected_genres') or []
        selected_genres = []
        for g in raw_selected_genres:
            if g in GENRE_KEYS and g != 'ALL' and g not in selected_genres:
                selected_genres.append(g)
        selected_genres = ['ALL'] + selected_genres
        genre_results = {g: [] for g in selected_genres}
        
        # ALL 장르: 전체 상위 4개
        if 'ALL' in genre_results:
            genre_results['ALL'] = [
                {
                    'song_id': song['song_id'],
                    'title': song.get('title', ''),
                    'artist': song.get('artist', ''),
                    'album_cover': song.get('album_cover'),
                    'bpm': song.get('bpm'),
                    'key': song.get('key'),
                    'score': song['score2']
                }
                for song in all_songs_sorted[:4]
            ]
            print(f"  - ALL: {len(genre_results['ALL'])}곡 (전체 상위)")
        
        # 나머지 장르별 결과
        for song in scored_songs:
            for genre in song['genres']:
                # 장르명을 대문자로 변환하여 매칭
                genre_upper = genre.upper()
                if genre_upper in genre_results and genre_upper != 'ALL':
                    genre_results[genre_upper].append({
                        'song_id': song['song_id'],
                        'title': song.get('title', ''),
                        'artist': song.get('artist', ''),
                        'album_cover': song.get('album_cover'),
                        'bpm': song.get('bpm'),
                        'key': song.get('key'),
                        'score': song['score2']
                    })
        
        # 각 장르별로 정렬 및 top4 추출 (ALL 제외)
        for genre in genre_results:
            if genre != 'ALL':
                genre_results[genre].sort(key=lambda x: x['score'], reverse=True)
                genre_results[genre] = genre_results[genre][:4]
                print(f"  - {GENRE_KEY_TO_LABEL.get(genre, genre)}: {len(genre_results[genre])}곡")
        
        # 상황별 결과: 유저가 선택한 상황만 반영 (미선택 시 빈 결과)
        selected_situations = feedback.get('selected_situations') or []
        selected_situations = [s for s in selected_situations if s in SITUATION_KEYS]
        situation_results = {s: [] for s in selected_situations}
        for song in scored_songs:
            for situation in song['situations']:
                if situation in situation_results:
                    situation_results[situation].append({
                        'song_id': song['song_id'],
                        'title': song.get('title', ''),
                        'artist': song.get('artist', ''),
                        'album_cover': song.get('album_cover'),
                        'bpm': song.get('bpm'),
                        'key': song.get('key'),
                        'score': song['score2']
                    })
        
        # 각 상황별로 정렬 및 top4 추출
        for situation in situation_results:
            situation_results[situation].sort(key=lambda x: x['score'], reverse=True)
            situation_results[situation] = situation_results[situation][:4]
            print(f"  - {situation}: {len(situation_results[situation])}곡")
        
        # Step 7: DB에 저장
        print("\n[Step 7] 2차 추천 결과 저장")
        # 장르 키를 내부 enum에서 표시 라벨로 변환해서 저장
        genre_results_labeled = {
            GENRE_KEY_TO_LABEL.get(k, k): v
            for k, v in genre_results.items()
        }
        recommend_songs = {
            'genre_recommendations': genre_results_labeled,
            'situation_recommendations': situation_results
        }
        
        try:
            supabase.table("recommendation_logs").update({
                'recommend_songs': recommend_songs,
                'updated_at': datetime.now().isoformat()
            }).eq("id", job_id).execute()
            print(f"✓ recommend_songs 저장 완료")
        except Exception as e:
            # 구 스키마 호환: recommended_songs
            print(f"⚠️  recommend_songs 저장 실패, 구 컬럼으로 재시도: {e}")
            try:
                supabase.table("recommendation_logs").update({
                    'recommended_songs': recommend_songs,
                    'updated_at': datetime.now().isoformat()
                }).eq("id", job_id).execute()
                print("✓ recommended_songs 저장 완료")
            except Exception as e2:
                print(f"⚠️  2차 추천 결과 저장 실패(신/구 컬럼 모두): {e2}")
        
        # Status 업데이트: DONE
        update_recommendation_status(supabase, job_id, STATUS_DONE)
        
        print("\n" + "="*70)
        print("✅ 2차 추천 완료 (DONE 상태로 전환)")
        print("="*70)
        
        return {
            'status': 'success',
            'job_id': job_id,
            'genre_results': {k: len(v) for k, v in genre_results.items()},
            'situation_results': {k: len(v) for k, v in situation_results.items()}
        }
        
    except Exception as e:
        print(f"\n❌ 2차 추천 처리 실패: {e}")
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


# CLI 실행
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="2차 추천 워커"
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
    
    args = parser.parse_args()
    
    try:
        result = process_second_recommendation(
            job_id=args.job_id,
            user_id=args.user_id
        )
        
        if result.get('status') == 'success':
            print("\n✅ 2차 추천 완료!")
            exit(0)
        else:
            print(f"\n❌ 2차 추천 실패: {result.get('error', 'Unknown error')}")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


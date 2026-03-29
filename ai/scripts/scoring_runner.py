"""
유저-노래 점수 계산기

유저 특징과 곡 특징을 읽어서 점수를 계산하고 랭킹 생성
"""
import json
import csv
import numpy as np
from pathlib import Path
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')


def hz_to_semitone(hz: float) -> float:
    """Hz를 MIDI note number (semitone)로 변환"""
    if hz <= 0:
        return 0.0
    return 12 * np.log2(hz / 440.0) + 69.0


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity 계산"""
    a_norm = a / (np.linalg.norm(a) + 1e-8)
    b_norm = b / (np.linalg.norm(b) + 1e-8)
    return float(np.dot(a_norm, b_norm))


def calculate_ecapa_score(
    user_embedding: np.ndarray,
    song_embedding: np.ndarray,
    sim_low: float = 0.35,
    sim_high: float = 0.90
) -> Dict:
    """
    ECAPA 유사도 점수 계산 (클립+리스케일)
    
    Returns:
        {ecapa_sim, ecapa_score}
    """
    # Cosine similarity
    ecapa_sim = cosine_similarity(user_embedding, song_embedding)
    
    # Clip
    ecapa_clipped = np.clip(ecapa_sim, sim_low, sim_high)
    
    # Rescale to 0~1
    ecapa_score = (ecapa_clipped - sim_low) / (sim_high - sim_low)
    
    return {
        'ecapa_sim': float(ecapa_sim),
        'ecapa_score': float(ecapa_score)
    }


def calculate_pitch_score(
    user_pitch: Dict,
    song_pitch: Dict,
    σh: float = 3.0,
    σl: float = 7.0,  # 저음 페널티 약하게 (4.0 → 7.0)
    w_feasible: float = 0.85,
    w_comfort: float = 0.15
) -> Dict:
    """
    음역대 유사도 점수 계산 (가중합 방식)
    
    Args:
        user_pitch: {f0_p25, f0_p75, f0_p2, f0_p98} (유저는 p2/p98 사용)
        song_pitch: {f0_p25, f0_p75, f0_p5, f0_p95} (곡은 p5/p95 사용)
    
    Returns:
        {pitch_comfort, pitch_feasible, pitch_total, ...}
    """
    # 1. 테시투라 오버랩 (IoU 방식) → pitch_comfort
    user_tessitura = [user_pitch['f0_p25'], user_pitch['f0_p75']]
    song_tessitura = [song_pitch['f0_p25'], song_pitch['f0_p75']]
    
    overlap_start = max(user_tessitura[0], song_tessitura[0])
    overlap_end = min(user_tessitura[1], song_tessitura[1])
    overlap_length = max(0, overlap_end - overlap_start)
    
    user_tessitura_length = user_tessitura[1] - user_tessitura[0]
    song_tessitura_length = song_tessitura[1] - song_tessitura[0]
    
    # IoU 방식: 교집합 / 합집합
    union_length = user_tessitura_length + song_tessitura_length - overlap_length
    if union_length > 0:
        pitch_comfort = overlap_length / union_length
    else:
        pitch_comfort = 0.0
    
    # 2. Range coverage (세미톤 기반 가우시안) → pitch_feasible
    # 유저는 p2/p98 사용 (더 robust)
    user_high_st = hz_to_semitone(user_pitch.get('f0_p98', user_pitch.get('f0_p95', 0)))
    user_low_st = hz_to_semitone(user_pitch.get('f0_p2', user_pitch.get('f0_p5', 0)))
    # 곡은 p5/p95 사용 (기존 유지)
    song_high_st = hz_to_semitone(song_pitch['f0_p95'])
    song_low_st = hz_to_semitone(song_pitch['f0_p5'])
    
    # 고음: 곡이 유저보다 높으면 페널티 (못 부르면 치명적)
    delta_high_st = max(0, song_high_st - user_high_st)
    
    # 저음: 곡이 유저보다 낮으면 페널티 (유저가 못 내려가면 문제)
    delta_low_st = max(0, song_low_st - user_low_st)
    
    pitch_feasible = np.exp(
        - (delta_high_st / σh)**2 
        - (delta_low_st / σl)**2
    )
    
    # 3. 가중합 방식 (곱 금지: 0으로 죽음 방지)
    pitch_total = w_feasible * pitch_feasible + w_comfort * pitch_comfort
    
    return {
        'pitch_comfort': float(pitch_comfort),
        'pitch_feasible': float(pitch_feasible),
        'pitch_total': float(pitch_total),
        # 하위 호환성을 위해 기존 키도 유지
        'tessitura_overlap': float(pitch_comfort),
        'range_coverage': float(pitch_feasible),
        'pitch_score': float(pitch_total),
        # 디버깅용 정보
        'user_p2': user_pitch.get('f0_p2', user_pitch.get('f0_p5', 0)),
        'user_p98': user_pitch.get('f0_p98', user_pitch.get('f0_p95', 0)),
        'user_p5': user_pitch.get('f0_p5', 0),
        'user_p95': user_pitch.get('f0_p95', 0),
        'song_p5': song_pitch['f0_p5'],
        'song_p95': song_pitch['f0_p95'],
        'range_gap_semitone_high': float(delta_high_st),
        'range_gap_semitone_low': float(delta_low_st)
    }


def calculate_timbre_score(
    user_timbre: Dict,
    song_timbre: Dict,
    σ_normalized: float = 0.15,
    σ_formant: float = 0.5,
    σ_spectral: float = 500.0,
    σ_f0_mean: float = 100.0
) -> Dict:
    """
    음색 프로파일 유사도 점수 계산 (exp 기반)
    
    Returns:
        {timbre_score, ...}
    """
    # 1. 정규화된 특성 (0~1 스케일)
    normalized_features = ['brightness', 'roughness', 'body', 'clarity', 'warmth']
    feature_similarities = []
    
    for feature in normalized_features:
        if feature in user_timbre and feature in song_timbre:
            diff = abs(user_timbre[feature] - song_timbre[feature])
            sim = np.exp(-diff / σ_normalized)
            feature_similarities.append(sim)
    
    normalized_similarity = np.mean(feature_similarities) if feature_similarities else 0.0
    
    # 2. Formant (F1, F2)
    if 'formant_f1' in user_timbre and 'formant_f1' in song_timbre:
        formant_f1_diff = abs(user_timbre['formant_f1'] - song_timbre['formant_f1'])
        formant_f2_diff = abs(user_timbre['formant_f2'] - song_timbre['formant_f2'])
        formant_distance = np.sqrt(
            (formant_f1_diff / 500)**2 + 
            (formant_f2_diff / 1000)**2
        )
        formant_similarity = np.exp(-formant_distance / σ_formant)
    else:
        formant_similarity = 0.0
    
    # 3. Spectral Centroid
    if 'spectral_centroid' in user_timbre and 'spectral_centroid' in song_timbre:
        spectral_diff = abs(user_timbre['spectral_centroid'] - song_timbre['spectral_centroid'])
        spectral_similarity = np.exp(-spectral_diff / σ_spectral)
    else:
        spectral_similarity = 0.0
    
    # 4. f0_mean (비중 낮게)
    if 'f0_mean' in user_timbre and 'f0_mean' in song_timbre:
        f0_mean_diff = abs(user_timbre['f0_mean'] - song_timbre['f0_mean'])
        f0_mean_similarity = np.exp(-f0_mean_diff / σ_f0_mean)
    else:
        f0_mean_similarity = 0.0
    
    # 5. 가중 평균
    timbre_score = (
        0.5 * normalized_similarity +
        0.3 * formant_similarity +
        0.15 * spectral_similarity +
        0.05 * f0_mean_similarity
    )
    
    return {
        'timbre_score': float(timbre_score),
        'normalized_similarity': float(normalized_similarity),
        'formant_similarity': float(formant_similarity),
        'spectral_similarity': float(spectral_similarity),
        'f0_mean_similarity': float(f0_mean_similarity)
    }


def calculate_final_score(
    ecapa_score: float,
    pitch_total: float,
    timbre_score: float,
    w_ecapa: float = 0.30,
    w_pitch: float = 0.55,
    w_timbre: float = 0.15,
    γ: float = 0.7
) -> float:
    """
    최종 점수 계산 (가중합 + soft penalty)
    
    Args:
        ecapa_score: ECAPA 점수
        pitch_total: 음역대 총점 (pitch_feasible + pitch_comfort의 가중합)
        timbre_score: 음색 점수
        w_ecapa, w_pitch, w_timbre: 가중치
        γ: soft penalty 지수
    
    Returns:
        final_score: 최종 점수
    """
    # 가중합
    final_score_base = (
        w_ecapa * ecapa_score +
        w_pitch * pitch_total +
        w_timbre * timbre_score
    )
    
    # Soft penalty (안전장치: pitch_total이 너무 낮으면 penalty 완화)
    # pitch_total이 0.05 미만이면 penalty를 거의 주지 않음
    if pitch_total < 0.05:
        penalty_factor = 0.5  # 최소 페널티 (pitch가 매우 낮아도 완전히 죽이지 않음)
    else:
        penalty_factor = pitch_total ** γ
    
    final_score = final_score_base * penalty_factor
    
    return float(final_score)


def score_song(user_features: Dict, song_features: Dict) -> Dict:
    """
    단일 곡에 대한 점수 계산
    
    Args:
        user_features: 유저 특징
        song_features: 곡 특징
    
    Returns:
        score_result: 점수 결과 딕셔너리
    """
    # ECAPA 점수
    user_embedding = np.array(user_features['representative_embedding'])
    song_embedding = np.array(song_features['song_repr_embedding'])
    ecapa_result = calculate_ecapa_score(user_embedding, song_embedding)
    
    # Pitch 점수
    # 유저 특징에서 퍼센타일 정보 사용
    # 유저는 p2/p98 사용 (더 robust, 옥타브 에러/샘플 편향에 덜 취약)
    user_pitch_profile = user_features['pitch_profile']
    
    # 퍼센타일이 있으면 사용, 없으면 f0_min/max 또는 features에서 계산
    if 'f0_p2' in user_pitch_profile and 'f0_p98' in user_pitch_profile:
        # p2/p98 정보가 있는 경우 (최신 형식)
        user_pitch = {
            'f0_p2': user_pitch_profile['f0_p2'],
            'f0_p98': user_pitch_profile['f0_p98'],
            'f0_p25': user_pitch_profile['f0_p25'],
            'f0_p75': user_pitch_profile['f0_p75'],
            # 하위 호환성
            'f0_p5': user_pitch_profile.get('f0_p5', user_pitch_profile['f0_p2']),
            'f0_p95': user_pitch_profile.get('f0_p95', user_pitch_profile['f0_p98'])
        }
    elif 'f0_p5' in user_pitch_profile:
        # p5/p95만 있는 경우 (기존 형식) - p2/p98로 근사
        user_pitch = {
            'f0_p2': user_pitch_profile.get('f0_p2', user_pitch_profile['f0_p5'] * 0.95),  # p5보다 약간 낮게
            'f0_p98': user_pitch_profile.get('f0_p98', user_pitch_profile['f0_p95'] * 1.02),  # p95보다 약간 높게
            'f0_p25': user_pitch_profile['f0_p25'],
            'f0_p75': user_pitch_profile['f0_p75'],
            'f0_p5': user_pitch_profile['f0_p5'],
            'f0_p95': user_pitch_profile['f0_p95']
        }
    elif 'features' in user_features and 'pitch' in user_features['features']:
        # features.pitch에서 f0_contour로 퍼센타일 계산
        pitch_data = user_features['features']['pitch']
        f0_contour = np.array(pitch_data.get('f0_contour', []))
        voiced_mask = np.array(pitch_data.get('voiced_mask', f0_contour > 0))
        f0_voiced = f0_contour[(f0_contour > 0) & voiced_mask]
        
        if len(f0_voiced) > 0:
            user_pitch = {
                'f0_p2': float(np.percentile(f0_voiced, 2)),
                'f0_p98': float(np.percentile(f0_voiced, 98)),
                'f0_p25': float(np.percentile(f0_voiced, 25)),
                'f0_p75': float(np.percentile(f0_voiced, 75)),
                # 하위 호환성
                'f0_p5': float(np.percentile(f0_voiced, 5)),
                'f0_p95': float(np.percentile(f0_voiced, 95))
            }
        else:
            # f0_voiced가 없으면 f0_min/max 사용
            f0_min = user_pitch_profile.get('f0_min', 0.0)
            f0_max = user_pitch_profile.get('f0_max', 0.0)
            tessitura_low = user_pitch_profile.get('tessitura_low', f0_min)
            tessitura_high = user_pitch_profile.get('tessitura_high', f0_max)
            # f0_voiced가 없으면 f0_min/max 보수적 근사
            user_pitch = {
                'f0_p2': f0_min * 0.95 if f0_min > 0 else 0.0,   # 5% 낮게
                'f0_p98': f0_max * 1.01 if f0_max > 0 else 0.0,  # 1% 높게 (보수적)
                'f0_p25': tessitura_low,
                'f0_p75': tessitura_high,
                'f0_p5': f0_min * 0.9 if f0_min > 0 else 0.0,
                'f0_p95': f0_max * 0.98 if f0_max > 0 else 0.0
            }
    else:
        # f0_min/max만 있는 경우: 보수적으로 근사
        f0_min = user_pitch_profile.get('f0_min', 0.0)
        f0_max = user_pitch_profile.get('f0_max', 0.0)
        tessitura_low = user_pitch_profile.get('tessitura_low', f0_min)
        tessitura_high = user_pitch_profile.get('tessitura_high', f0_max)
        
        # 보수적 근사 규칙:
        # - f0_p98: f0_max보다 약간 높게 (옥타브 에러 고려)
        # - f0_p2: f0_min보다 약간 낮게 (저음은 영향 적게)
        user_pitch = {
            'f0_p2': f0_min * 0.95 if f0_min > 0 else 0.0,   # 5% 낮게
            'f0_p98': f0_max * 1.01 if f0_max > 0 else 0.0,  # 1% 높게 (보수적)
            'f0_p25': tessitura_low,
            'f0_p75': tessitura_high,
            'f0_p5': f0_min * 0.9 if f0_min > 0 else 0.0,
            'f0_p95': f0_max * 0.98 if f0_max > 0 else 0.0
        }
    song_pitch = {
        'f0_p5': song_features['f0_p5'],
        'f0_p25': song_features['f0_p25'],
        'f0_p75': song_features['f0_p75'],
        'f0_p95': song_features['f0_p95']
    }
    pitch_result = calculate_pitch_score(user_pitch, song_pitch)
    
    # Timbre 점수
    timbre_result = calculate_timbre_score(
        user_features['timbre_vector'],
        song_features['timbre']
    )
    
    # 최종 점수
    final_score = calculate_final_score(
        ecapa_result['ecapa_score'],
        pitch_result['pitch_total'],
        timbre_result['timbre_score']
    )
    
    # 결과 구성 (디버깅용 중간값 포함)
    result = {
        'song_id': song_features['song_id'],
        'final_score': final_score,
        
        # ECAPA 점수
        **ecapa_result,
        'ecapa_sim_raw': ecapa_result['ecapa_sim'],  # 원본 유사도
        
        # Pitch 점수
        **pitch_result,
        'user_p2': user_pitch.get('f0_p2', 0),
        'user_p98': user_pitch.get('f0_p98', 0),
        'user_p5': user_pitch.get('f0_p5', 0),
        'user_p95': user_pitch.get('f0_p95', 0),
        'song_p5': song_pitch['f0_p5'],
        'song_p95': song_pitch['f0_p95'],
        'delta_high_st': pitch_result['range_gap_semitone_high'],
        'delta_low_st': pitch_result['range_gap_semitone_low'],
        
        # Timbre 점수
        **timbre_result,
        
        # 메타데이터
        'voiced_ratio_user': user_features.get('voiced_ratio', 0.0),
        'voiced_ratio_song': song_features.get('voiced_ratio', 0.0)
    }
    
    return result


def load_user_features(user_features_path: str) -> Dict:
    """
    유저 특징 로드 (여러 키 형식 지원)
    
    지원하는 키 형식:
    - 'embedding' (user_vocal_pipeline 출력)
    - 'representative_embedding' (직접 구조)
    - 'ecapa_embedding' (대체 키)
    """
    with open(user_features_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 여러 키 형식 시도
    embedding_keys = ['embedding', 'representative_embedding', 'ecapa_embedding']
    embedding_data = None
    
    for key in embedding_keys:
        if key in data:
            embedding_data = data[key]
            break
    
    if embedding_data is None:
        # 직접 구조인 경우
        if 'representative_embedding' in data:
            return data
        else:
            available_keys = ', '.join(data.keys()[:5])
            raise ValueError(
                f"유저 특징 파일 형식을 인식할 수 없습니다.\n"
                f"필요한 키: 'embedding' 또는 'representative_embedding'\n"
                f"파일에 있는 키: {available_keys}..."
            )
    
    # embedding 구조에서 추출
    if isinstance(embedding_data, dict):
        user_features = {
            'representative_embedding': embedding_data.get('representative_embedding', embedding_data),
            'pitch_profile': embedding_data.get('pitch_profile', {}),
            'timbre_vector': embedding_data.get('timbre_vector', {})
        }
    else:
        # 리스트인 경우 (직접 임베딩)
        user_features = {
            'representative_embedding': embedding_data,
            'pitch_profile': data.get('pitch_profile', {}),
            'timbre_vector': data.get('timbre_vector', {})
        }
    
    # features도 함께 로드 (퍼센타일 계산용)
    if 'features' in data:
        user_features['features'] = data['features']
    
    # voiced_ratio 추출
    # test2_result.json에는 직접 저장되지 않으므로 features에서 계산 필요
    # 일단 기본값으로 설정 (나중에 features.pitch에서 계산 가능)
    if 'features' in data and 'pitch' in data['features']:
        # features.pitch에서 voiced_mask로 계산
        pitch_data = data['features']['pitch']
        if 'voiced_mask' in pitch_data:
            voiced_mask = np.array(pitch_data['voiced_mask'])
            user_features['voiced_ratio'] = float(np.sum(voiced_mask) / len(voiced_mask)) if len(voiced_mask) > 0 else 0.0
        else:
            user_features['voiced_ratio'] = 0.0
    else:
        # 기본값 설정
        user_features['voiced_ratio'] = 0.0
    
    return user_features


def load_song_features(song_features_dir: str) -> List[Dict]:
    """곡 특징들 로드"""
    features_dir = Path(song_features_dir)
    if not features_dir.exists():
        raise ValueError(f"곡 특징 디렉토리가 없습니다: {song_features_dir}")
    
    song_files = list(features_dir.glob("*.json"))
    if not song_files:
        raise ValueError(f"곡 특징 파일을 찾을 수 없습니다: {song_features_dir}")
    
    features_list = []
    for song_file in song_files:
        with open(song_file, 'r', encoding='utf-8') as f:
            features = json.load(f)
            features_list.append(features)
    
    return features_list


def run_scoring(
    user_features_path: str,
    song_features_dir: str,
    output_dir: str = "results"
) -> List[Dict]:
    """
    점수 계산 실행
    
    Args:
        user_features_path: 유저 특징 파일 경로
        song_features_dir: 곡 특징 디렉토리
        output_dir: 출력 디렉토리
    
    Returns:
        results: 점수 결과 리스트
    """
    print("\n" + "="*70)
    print("🎯 유저-노래 점수 계산")
    print("="*70)
    
    # 1. 특징 로드
    print("\n[Step 1] 특징 로드")
    user_features = load_user_features(user_features_path)
    print(f"✓ 유저 특징 로드: {user_features_path}")
    
    song_features_list = load_song_features(song_features_dir)
    print(f"✓ 곡 특징 로드: {len(song_features_list)}개")
    
    # 2. 점수 계산
    print("\n[Step 2] 점수 계산")
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
    
    # 3. 정렬
    print("\n[Step 3] 정렬")
    results_sorted = sorted(results, key=lambda x: x['final_score'], reverse=True)
    
    # 4. 저장
    print("\n[Step 4] 결과 저장")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 4-1. scores.csv
    csv_file = output_path / "scores.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if results_sorted:
            fieldnames = list(results_sorted[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results_sorted)
    print(f"✓ scores.csv 저장: {csv_file}")
    
    # 4-2. ranked.json
    json_file = output_path / "ranked.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results_sorted, f, indent=2, ensure_ascii=False)
    print(f"✓ ranked.json 저장: {json_file}")
    
    # 5. 요약 출력
    print("\n" + "="*70)
    print("📊 랭킹 결과 (상위 5개)")
    print("="*70)
    for i, result in enumerate(results_sorted[:5], 1):
        print(f"{i}. {result['song_id']}: {result['final_score']:.4f}")
        print(f"   ECAPA: {result.get('ecapa_score', 0):.4f}, "
              f"Pitch: {result.get('pitch_total', result.get('pitch_score', 0)):.4f}, "
              f"Timbre: {result.get('timbre_score', 0):.4f}")
    print("="*70 + "\n")
    
    return results_sorted


# CLI 실행
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="유저-노래 점수 계산기"
    )
    parser.add_argument(
        "--user",
        type=str,
        required=True,
        help="유저 특징 파일 경로"
    )
    parser.add_argument(
        "--songs",
        type=str,
        required=True,
        help="곡 특징 디렉토리"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="results",
        help="출력 디렉토리 (기본값: results)"
    )
    
    args = parser.parse_args()
    
    try:
        results = run_scoring(
            user_features_path=args.user,
            song_features_dir=args.songs,
            output_dir=args.out
        )
        
        print("\n✅ 처리 완료!")
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


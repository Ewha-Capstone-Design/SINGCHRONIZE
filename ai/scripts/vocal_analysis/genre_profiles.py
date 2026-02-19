"""
장르별 프로파일 데이터
- 각 장르의 특징적인 음역대, 음색, 발성 스타일 정의
"""
import numpy as np

# 장르별 프로파일
# 실제 데이터는 곡 DB에서 통계를 내서 업데이트해야 함
# 현재는 일반적인 장르 특성 기반 초기값

GENRE_PROFILES = {
    "발라드": {
        "name": "발라드",
        "description": "감성적이고 서정적인 곡",
        
        # 음역대 특성 (Hz)
        "pitch": {
            "typical_low": 130.8,   # C3
            "typical_high": 523.3,  # C5
            "tessitura_center": 261.6,  # C4 (중음역 중심)
            "range_semitones": 24.0  # 2옥타브
        },
        
        # 음색 특성 (0~1)
        "timbre": {
            "brightness": 0.5,      # 중간 밝기
            "roughness": 0.2,       # 부드러움
            "body": 0.6,            # 적당한 바디
            "clarity": 0.8,         # 높은 선명도
            "warmth": 0.7           # 따뜻함
        },
        
        # 발성 특성
        "vocal_style": {
            "pitch_stability": 0.8,     # 높은 음정 안정성 요구
            "breath_control": 0.8,      # 높은 호흡 조절 요구
            "dynamic_range": 0.7        # 다이나믹 표현 중요
        },
        
        # 가중치 (추천 시 각 요소의 중요도)
        "weights": {
            "pitch": 0.3,
            "timbre": 0.4,
            "vocal_style": 0.3
        }
    },
    
    "댄스": {
        "name": "댄스",
        "description": "경쾌하고 리드미컬한 곡",
        
        "pitch": {
            "typical_low": 146.8,   # D3
            "typical_high": 587.3,  # D5
            "tessitura_center": 293.7,  # D4 (약간 높은 음역)
            "range_semitones": 24.0
        },
        
        "timbre": {
            "brightness": 0.8,      # 밝고 화사함
            "roughness": 0.3,       # 약간의 에지
            "body": 0.5,            # 가벼운 바디
            "clarity": 0.7,         # 선명함
            "warmth": 0.4           # 차가운 느낌
        },
        
        "vocal_style": {
            "pitch_stability": 0.7,
            "breath_control": 0.6,
            "dynamic_range": 0.6
        },
        
        "weights": {
            "pitch": 0.2,
            "timbre": 0.5,
            "vocal_style": 0.3
        }
    },
    
    "R&B": {
        "name": "R&B/어반",
        "description": "그루브감 있고 소울풀한 곡",
        
        "pitch": {
            "typical_low": 110.0,   # A2
            "typical_high": 440.0,  # A4
            "tessitura_center": 220.0,  # A3 (낮은 음역)
            "range_semitones": 24.0
        },
        
        "timbre": {
            "brightness": 0.4,      # 어두운 음색
            "roughness": 0.4,       # 약간 거친 질감
            "body": 0.7,            # 두꺼운 바디
            "clarity": 0.6,         # 중간 선명도
            "warmth": 0.8           # 매우 따뜻함
        },
        
        "vocal_style": {
            "pitch_stability": 0.6,     # 비브라토 등 변화 많음
            "breath_control": 0.7,
            "dynamic_range": 0.8        # 다이나믹 표현 중요
        },
        
        "weights": {
            "pitch": 0.3,
            "timbre": 0.5,
            "vocal_style": 0.2
        }
    },
    
    "POP": {
        "name": "POP",
        "description": "대중적이고 다양한 스타일",
        
        "pitch": {
            "typical_low": 130.8,   # C3
            "typical_high": 523.3,  # C5
            "tessitura_center": 293.7,  # D4
            "range_semitones": 24.0
        },
        
        "timbre": {
            "brightness": 0.7,      # 밝음
            "roughness": 0.3,       # 부드러움
            "body": 0.5,            # 중간 바디
            "clarity": 0.7,         # 선명함
            "warmth": 0.5           # 중립
        },
        
        "vocal_style": {
            "pitch_stability": 0.7,
            "breath_control": 0.7,
            "dynamic_range": 0.6
        },
        
        "weights": {
            "pitch": 0.3,
            "timbre": 0.4,
            "vocal_style": 0.3
        }
    },
    
    "트로트": {
        "name": "트로트",
        "description": "한국 전통 대중가요",
        
        "pitch": {
            "typical_low": 146.8,   # D3
            "typical_high": 587.3,  # D5
            "tessitura_center": 329.6,  # E4 (높은 음역)
            "range_semitones": 24.0
        },
        
        "timbre": {
            "brightness": 0.6,      # 약간 밝음
            "roughness": 0.3,       # 부드러움
            "body": 0.6,            # 적당한 바디
            "clarity": 0.7,         # 선명함
            "warmth": 0.6           # 따뜻함
        },
        
        "vocal_style": {
            "pitch_stability": 0.6,     # 비브라토 많음
            "breath_control": 0.8,      # 높은 호흡 조절
            "dynamic_range": 0.7
        },
        
        "weights": {
            "pitch": 0.4,           # 음역대 중요
            "timbre": 0.3,
            "vocal_style": 0.3
        }
    },
    
    "락/메탈": {
        "name": "락/메탈",
        "description": "강렬하고 파워풀한 곡",
        
        "pitch": {
            "typical_low": 110.0,   # A2
            "typical_high": 587.3,  # D5
            "tessitura_center": 261.6,  # C4
            "range_semitones": 30.0     # 넓은 음역
        },
        
        "timbre": {
            "brightness": 0.5,      # 중간 밝기
            "roughness": 0.7,       # 거친 질감
            "body": 0.8,            # 두꺼운 바디
            "clarity": 0.5,         # 낮은 선명도 (왜곡)
            "warmth": 0.4           # 차가움
        },
        
        "vocal_style": {
            "pitch_stability": 0.6,
            "breath_control": 0.7,
            "dynamic_range": 0.9        # 매우 다이나믹
        },
        
        "weights": {
            "pitch": 0.2,
            "timbre": 0.6,          # 음색 매우 중요
            "vocal_style": 0.2
        }
    },
    
    "JPOP": {
        "name": "JPOP",
        "description": "일본 대중음악",
        
        "pitch": {
            "typical_low": 146.8,   # D3
            "typical_high": 587.3,  # D5
            "tessitura_center": 329.6,  # E4 (높은 음역)
            "range_semitones": 24.0
        },
        
        "timbre": {
            "brightness": 0.8,      # 매우 밝음
            "roughness": 0.2,       # 매우 부드러움
            "body": 0.4,            # 가벼운 바디
            "clarity": 0.8,         # 높은 선명도
            "warmth": 0.5           # 중립
        },
        
        "vocal_style": {
            "pitch_stability": 0.7,
            "breath_control": 0.7,
            "dynamic_range": 0.6
        },
        
        "weights": {
            "pitch": 0.3,
            "timbre": 0.5,
            "vocal_style": 0.2
        }
    },
    
    "인디": {
        "name": "인디",
        "description": "독립적이고 개성 있는 음악",
        
        "pitch": {
            "typical_low": 110.0,   # A2
            "typical_high": 523.3,  # C5
            "tessitura_center": 220.0,  # A3
            "range_semitones": 27.0
        },
        
        "timbre": {
            "brightness": 0.5,      # 중간
            "roughness": 0.5,       # 중간 (다양함)
            "body": 0.5,            # 중간
            "clarity": 0.6,         # 중간
            "warmth": 0.6           # 약간 따뜻함
        },
        
        "vocal_style": {
            "pitch_stability": 0.6,
            "breath_control": 0.6,
            "dynamic_range": 0.7
        },
        
        "weights": {
            "pitch": 0.2,
            "timbre": 0.5,
            "vocal_style": 0.3
        }
    }
}


def get_genre_list():
    """사용 가능한 장르 목록 반환"""
    return list(GENRE_PROFILES.keys())


def get_genre_profile(genre: str):
    """특정 장르의 프로파일 반환"""
    return GENRE_PROFILES.get(genre, None)


def calculate_pitch_distance(user_pitch: dict, genre_pitch: dict) -> float:
    """
    음역대 거리 계산
    
    Args:
        user_pitch: 유저 음역대 정보
        genre_pitch: 장르 음역대 정보
    
    Returns:
        distance (0~1, 낮을수록 가까움)
    """
    # 테시투라 중심 거리
    user_center = (user_pitch['tessitura_low'] + user_pitch['tessitura_high']) / 2
    genre_center = genre_pitch['tessitura_center']
    
    # 반음 단위로 변환
    center_distance = abs(12 * np.log2(user_center / genre_center))
    
    # 음역대 범위 차이
    user_range = user_pitch.get('range_semitones', 24.0)
    genre_range = genre_pitch['range_semitones']
    range_diff = abs(user_range - genre_range)
    
    # 정규화 (0~1)
    # 중심 거리: 12반음(1옥타브) 이상이면 1.0
    center_score = min(center_distance / 12.0, 1.0)
    # 범위 차이: 12반음 이상이면 1.0
    range_score = min(range_diff / 12.0, 1.0)
    
    # 가중 평균
    distance = center_score * 0.7 + range_score * 0.3
    
    return distance


def calculate_timbre_distance(user_timbre: dict, genre_timbre: dict) -> float:
    """
    음색 거리 계산 (유클리드 거리)
    
    Args:
        user_timbre: 유저 음색 벡터
        genre_timbre: 장르 음색 벡터
    
    Returns:
        distance (0~1, 낮을수록 가까움)
    """
    # 5차원 벡터
    user_vec = np.array([
        user_timbre['brightness'],
        user_timbre['roughness'],
        user_timbre['body'],
        user_timbre['clarity'],
        user_timbre['warmth']
    ])
    
    genre_vec = np.array([
        genre_timbre['brightness'],
        genre_timbre['roughness'],
        genre_timbre['body'],
        genre_timbre['clarity'],
        genre_timbre['warmth']
    ])
    
    # 유클리드 거리
    distance = np.linalg.norm(user_vec - genre_vec)
    
    # 정규화 (최대 거리는 √5 ≈ 2.236)
    normalized_distance = distance / np.sqrt(5)
    
    return normalized_distance


def calculate_vocal_style_distance(user_radar: dict, genre_style: dict) -> float:
    """
    발성 스타일 거리 계산
    
    Args:
        user_radar: 유저 레이더 차트 (0~100)
        genre_style: 장르 발성 스타일 (0~1)
    
    Returns:
        distance (0~1, 낮을수록 가까움)
    """
    # 레이더 차트를 0~1로 정규화
    user_pitch_stability = user_radar['pitch_stability'] / 100.0
    
    # breath_control은 레이더 차트에 없으므로 dynamic_control 사용
    # 또는 genre_style의 breath_control과 비교하기 위해 dynamic_control을 사용
    user_dynamic_control = user_radar.get('dynamic_control', 50.0) / 100.0
    
    # genre_style에는 breath_control이 있지만, 레이더 차트에는 dynamic_control만 있음
    # dynamic_control을 breath_control의 대리 지표로 사용
    user_breath_control = user_dynamic_control  # dynamic_control을 breath_control로 매핑
    
    # 다이나믹 레인지는 dynamic_control 사용
    user_dynamic_range = user_dynamic_control
    
    # 거리 계산
    distances = [
        abs(user_pitch_stability - genre_style['pitch_stability']),
        abs(user_breath_control - genre_style['breath_control']),
        abs(user_dynamic_range - genre_style['dynamic_range'])
    ]
    
    # 평균 거리
    distance = np.mean(distances)
    
    return distance



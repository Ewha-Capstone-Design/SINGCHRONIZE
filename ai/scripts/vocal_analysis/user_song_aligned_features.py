"""
유저 보컬 파이프라인 결과 → song_features 테이블과 동일 의미·이름의 스칼라/임베딩 필드.

- song_features를 수정하지 않고, user_vocal_profiles(및 analysis_jobs.result_data)에 같은 스키마로 적재해
  1차 추천(score_song)에서 파이프라인 재실행 없이 로드할 수 있게 함.
- F0 퍼센타일·voiced_ratio 계산은 song_feature_worker.extract_song_features 와 동일한 방식
  (전체 오디오 기준 f0_contour + voiced_mask).
- score_song 이 유저 쪽에서 쓰는 f0_p2 / f0_p98 은 song_features에는 없으므로 함께 저장(추가 컬럼·JSON).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np


def _f32(x: float) -> float:
    return float(np.float32(x))


def build_scoring_song_aligned_from_pipeline_result(
    pipeline_result: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    UserVocalPipeline.process() 결과(dict)에서 song_features 와 정렬된 피처 dict 생성.

    필수: pipeline_result['features'] (save_features=True)
    반환 키는 DB 컬럼명과 맞춤 (vocal_repr_embedding 은 song_repr_embedding 과 대응).
    """
    feats = pipeline_result.get("features")
    if not isinstance(feats, dict):
        return None

    emb_block = feats.get("embedding") or {}
    rep = emb_block.get("representative")
    if rep is None:
        return None
    if hasattr(rep, "tolist"):
        rep_list = [float(x) for x in rep.tolist()]
    else:
        rep_list = [float(x) for x in list(rep)]
    if len(rep_list) != 192:
        return None

    pitch = feats.get("pitch") or {}
    f0_contour = np.array(pitch.get("f0_contour", []))
    voiced_mask = np.array(pitch.get("voiced_mask", f0_contour > 0))
    f0_voiced = f0_contour[(f0_contour > 0) & voiced_mask]

    if len(voiced_mask) > 0:
        voiced_ratio = float(np.sum(voiced_mask) / len(voiced_mask))
    else:
        voiced_ratio = 0.0

    if len(f0_voiced) > 0:
        f0_p2 = _f32(np.percentile(f0_voiced, 2))
        f0_p5 = _f32(np.percentile(f0_voiced, 5))
        f0_p25 = _f32(np.percentile(f0_voiced, 25))
        f0_p50 = _f32(np.percentile(f0_voiced, 50))
        f0_p75 = _f32(np.percentile(f0_voiced, 75))
        f0_p95 = _f32(np.percentile(f0_voiced, 95))
        f0_p98 = _f32(np.percentile(f0_voiced, 98))
    else:
        f0_p2 = f0_p5 = f0_p25 = f0_p50 = f0_p75 = f0_p95 = f0_p98 = _f32(0.0)
        voiced_ratio = 0.0

    timbre_w = (feats.get("timbre") or {}).get("weighted") or {}

    out: Dict[str, Any] = {
        "vocal_repr_embedding": rep_list,
        "f0_p5": f0_p5,
        "f0_p25": f0_p25,
        "f0_p50": f0_p50,
        "f0_p75": f0_p75,
        "f0_p95": f0_p95,
        "f0_p2": f0_p2,
        "f0_p98": f0_p98,
        "voiced_ratio": _f32(voiced_ratio),
        "timbre_brightness": _f32(float(timbre_w.get("brightness", 0.0))),
        "timbre_roughness": _f32(float(timbre_w.get("roughness", 0.0))),
        "timbre_body": _f32(float(timbre_w.get("body", 0.0))),
        "timbre_clarity": _f32(float(timbre_w.get("clarity", 0.0))),
        "timbre_warmth": _f32(float(timbre_w.get("warmth", 0.0))),
        "timbre_f0_mean": _f32(float(timbre_w.get("f0_mean", 0.0))),
        "timbre_formant_f1": _f32(float(timbre_w.get("formant_f1", 0.0))),
        "timbre_formant_f2": _f32(float(timbre_w.get("formant_f2", 0.0))),
        "timbre_spectral_centroid": _f32(float(timbre_w.get("spectral_centroid", 0.0))),
    }
    return out


def vocal_repr_embedding_to_pgvector_str(embedding: List[float]) -> str:
    """song_feature_worker.save_features_to_db 와 동일한 pgvector 리터럴 문자열."""
    return "[" + ",".join(str(x) for x in embedding) + "]"


def try_user_features_from_db_profile_row(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    user_vocal_profiles 한 행(dict)에 song 정렬 스코어링 컬럼이 있으면 user_features 로 변환.
    컬럼이 없거나 불완전하면 None.
    """
    if not row:
        return None
    required = (
        "vocal_repr_embedding",
        "f0_p2",
        "f0_p5",
        "f0_p25",
        "f0_p50",
        "f0_p75",
        "f0_p95",
        "f0_p98",
        "voiced_ratio",
        "timbre_brightness",
        "timbre_roughness",
        "timbre_body",
        "timbre_clarity",
        "timbre_warmth",
        "timbre_f0_mean",
        "timbre_formant_f1",
        "timbre_formant_f2",
        "timbre_spectral_centroid",
    )
    for k in required:
        if k not in row or row[k] is None:
            return None
    try:
        return user_features_from_scoring_song_aligned(row)
    except (KeyError, TypeError, ValueError):
        return None


def user_features_from_scoring_song_aligned(aligned: Dict[str, Any]) -> Dict[str, Any]:
    """
    scoring_song_aligned (또는 user_vocal_profiles 의 동명 컬럼들) → score_song용 user_features.
    """
    emb = aligned.get("vocal_repr_embedding")
    if emb is None:
        raise ValueError("scoring_song_aligned.vocal_repr_embedding 이 없습니다.")
    if isinstance(emb, str):
        emb = emb.strip("[]").split(",")
        emb = [float(x.strip()) for x in emb if x.strip()]

    timbre_vector = {
        "brightness": float(aligned["timbre_brightness"]),
        "roughness": float(aligned["timbre_roughness"]),
        "body": float(aligned["timbre_body"]),
        "clarity": float(aligned["timbre_clarity"]),
        "warmth": float(aligned["timbre_warmth"]),
        "f0_mean": float(aligned["timbre_f0_mean"]),
        "formant_f1": float(aligned["timbre_formant_f1"]),
        "formant_f2": float(aligned["timbre_formant_f2"]),
        "spectral_centroid": float(aligned["timbre_spectral_centroid"]),
    }

    pitch_profile = {
        "f0_p2": float(aligned["f0_p2"]),
        "f0_p98": float(aligned["f0_p98"]),
        "f0_p25": float(aligned["f0_p25"]),
        "f0_p75": float(aligned["f0_p75"]),
        "f0_p5": float(aligned["f0_p5"]),
        "f0_p95": float(aligned["f0_p95"]),
    }

    return {
        "representative_embedding": list(emb),
        "pitch_profile": pitch_profile,
        "timbre_vector": timbre_vector,
        "voiced_ratio": float(aligned.get("voiced_ratio", 0.0)),
    }

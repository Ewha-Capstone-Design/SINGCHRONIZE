"""
analysis_jobs.result_data 저장용: 파이프라인 report 중 화면에 쓰는 블록만 `result` 키 아래에 담음.
embedding / metadata / genre_fitness.analysis.details / timbre formants 제외.

job_id, user_id, recording_id, created_at 등은 analysis_jobs 행 컬럼에 두고 result_data에는 넣지 않음.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict


def _to_json_value(obj: Any) -> Any:
    """numpy 스칼라·배열 등 JSON 직렬화 가능 형태로."""
    if isinstance(obj, dict):
        return {k: _to_json_value(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_json_value(v) for v in obj]
    if hasattr(obj, "tolist"):
        return _to_json_value(obj.tolist())
    if isinstance(obj, (float, int)) or obj is None:
        return obj
    if isinstance(obj, str):
        return obj
    try:
        return float(obj)
    except (TypeError, ValueError):
        return obj


def _slice_genre_fitness(gf: Dict[str, Any]) -> Dict[str, Any]:
    """scores, top_genres, best_match, best_score 만 (analysis.details 제외)."""
    if not gf:
        return {}
    analysis = gf.get("analysis") or {}
    out: Dict[str, Any] = {
        "scores": _to_json_value(gf.get("scores") or {}),
        "top_genres": _to_json_value(gf.get("top_genres") or []),
    }
    # 파이프라인은 analysis 안에 두지만, DB에는 최상위로 펼침
    out["best_match"] = gf.get("best_match", analysis.get("best_match"))
    out["best_score"] = _to_json_value(
        gf.get("best_score", analysis.get("best_score"))
    )
    return out


def _slice_timbre(tp: Dict[str, Any]) -> Dict[str, Any]:
    """formants 제외 (저장·전송 부담 큼)."""
    if not tp:
        return {}
    return {
        k: _to_json_value(v)
        for k, v in tp.items()
        if k != "formants"
    }


def _score_0_100(value: Any) -> int:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return 0
    if n < 0:
        return 0
    if n > 100:
        return 100
    return int(round(n))


def build_result_data_payload(pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Supabase result_data 컬럼에 넣을 dict.

    {
      "version": "v1",
      "result": {
        "radar_chart": {...},
        "vocal_range": {...},
        "genre_fitness": {...},
        "timbre_profile": {...}
      }
    }
    """
    report = pipeline_result.get("report") or {}
    radar = _to_json_value(report.get("radar_chart") or {})
    vocal_range = _to_json_value(report.get("vocal_range") or {})
    genre_fitness = _slice_genre_fitness(report.get("genre_fitness") or {})
    timbre_profile = _slice_timbre(report.get("timbre_profile") or {})
    curve = vocal_range.get("vocal_range_curve") if isinstance(vocal_range, dict) else {}
    comfort = curve.get("comfortable_range") if isinstance(curve, dict) else {}

    genre_scores = genre_fitness.get("scores") if isinstance(genre_fitness, dict) else {}
    genre_data = []
    if isinstance(genre_scores, dict):
        genre_data = [
            {"genre": str(genre), "score": _score_0_100(score)}
            for genre, score in genre_scores.items()
        ]
        genre_data.sort(key=lambda x: x["score"], reverse=True)

    best_genre = ""
    if isinstance(genre_fitness, dict):
        best_genre = str(genre_fitness.get("best_match") or "")
    if not best_genre and genre_data:
        best_genre = genre_data[0]["genre"]

    notes = curve.get("notes") if isinstance(curve, dict) else []
    scores = curve.get("scores") if isinstance(curve, dict) else []
    range_data = []
    if isinstance(notes, list) and isinstance(scores, list):
        range_data = [
            {"note": str(note), "score": _score_0_100(score)}
            for note, score in zip(notes, scores)
        ]

    shaped = {
        "updated_at": datetime.now().strftime("%Y.%m.%d"),
        "traits": [
            {"label": "음정 안정성", "value": _score_0_100(radar.get("pitch_stability"))},
            {"label": "발성 수준", "value": _score_0_100(radar.get("vocal_clarity"))},
            {"label": "리듬 안정성", "value": _score_0_100(radar.get("rhythm_stability"))},
            {"label": "호흡 안정성", "value": _score_0_100(radar.get("high_note_stability"))},
            {"label": "소리 밀도", "value": _score_0_100(radar.get("dynamic_control"))},
        ],
        "genreFit": {
            "bestGenre": best_genre,
            "data": genre_data,
        },
        "timbre": [
            {"label": "밝기", "value": _score_0_100((timbre_profile.get("brightness") or {}).get("display_score"))},
            {"label": "거칠기", "value": _score_0_100((timbre_profile.get("roughness") or {}).get("display_score"))},
            {"label": "두께감", "value": _score_0_100((timbre_profile.get("body") or {}).get("display_score"))},
            {"label": "선명도", "value": _score_0_100((timbre_profile.get("clarity") or {}).get("display_score"))},
            {"label": "따뜻함", "value": _score_0_100((timbre_profile.get("warmth") or {}).get("display_score"))},
        ],
        "range": {
            "comfort": {
                "from": str(comfort.get("low_note") or vocal_range.get("tessitura_low_note") or ""),
                "to": str(comfort.get("high_note") or vocal_range.get("tessitura_high_note") or ""),
            },
            "stats": {
                "max": str(vocal_range.get("highest_note") or ""),
                "avg": str(curve.get("peak_note") or ""),
                "min": str(vocal_range.get("lowest_note") or ""),
            },
            "data": range_data,
        },
    }
    # 기존 집계/동기화 로직과의 호환을 위해 내부 원본 블록도 함께 저장
    shaped["version"] = "v1"
    shaped["result"] = {
        "radar_chart": radar if isinstance(radar, dict) else {},
        "vocal_range": vocal_range if isinstance(vocal_range, dict) else {},
        "genre_fitness": genre_fitness if isinstance(genre_fitness, dict) else {},
        "timbre_profile": timbre_profile if isinstance(timbre_profile, dict) else {},
    }
    return shaped


def build_failure_result_data(error_message: str) -> Dict[str, Any]:
    """실패 시 result_data — 에러 문구만 (식별·시간은 analysis_jobs 컬럼)."""
    return {"version": "v1", "error": str(error_message)}

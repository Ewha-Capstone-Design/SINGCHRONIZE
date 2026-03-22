"""
analysis_jobs.result_data 저장용: 파이프라인 report 중 화면에 쓰는 블록만 `result` 키 아래에 담음.
embedding / metadata / genre_fitness.analysis.details / timbre formants 제외.

job_id, user_id, recording_id, created_at 등은 analysis_jobs 행 컬럼에 두고 result_data에는 넣지 않음.
"""
from __future__ import annotations

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
    radar = report.get("radar_chart") or {}
    vocal_range = report.get("vocal_range") or {}
    genre_fitness = _slice_genre_fitness(report.get("genre_fitness") or {})
    timbre_profile = _slice_timbre(report.get("timbre_profile") or {})

    inner = {
        "radar_chart": _to_json_value(radar) if radar else {},
        "vocal_range": _to_json_value(vocal_range) if vocal_range else {},
        "genre_fitness": genre_fitness,
        "timbre_profile": timbre_profile,
    }

    return {
        "version": "v1",
        "result": inner,
    }


def build_failure_result_data(error_message: str) -> Dict[str, Any]:
    """실패 시 result_data — 에러 문구만 (식별·시간은 analysis_jobs 컬럼)."""
    return {"version": "v1", "error": str(error_message)}

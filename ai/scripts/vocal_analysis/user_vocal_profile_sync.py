"""
완료된 analysis_jobs 여러 건을 읽어 user_vocal_profiles 1행을 갱신.

집계 정책 (프론트/기획과 맞출 때 이 모듈 주석이 기준)
---------------------------------------------------------------------------
• result_data: analysis_jobs 행의 version + result 만 사용. 식별·시간은 테이블 컬럼.

• observed_* (누적 관측 음역)
    최근 N건 완료 분석에서, 세션마다 측정된 lowest_hz / highest_hz 를 모은 뒤
    전체에 대해 min(lowest), max(highest).
    → “한 번은 낮은 곡만, 다른 번은 높은 곡만” 불렀을 때 폭이 넓어지는 효과.
    → “항상 이 범위를 안정적으로 낼 수 있다”는 뜻은 아님.

• stable_* (안정 음역)
    같은 N건에서 세션별 lowest_hz 의 중앙값, 세션별 highest_hz 의 중앙값.
    → 녹음·컨디션에 덜 흔들리는 대표 저·고음.

• stable_tessitura_*
    세션별 tessitura_low / tessitura_high 각각의 중앙값.
    → 테시투라는 “편하게 자주 내는 구간”에 가깝기 때문에 세션 간 min/max 로 넓히지 않음.

• radar_median_*
    최근 N건 완료 분석의 레이더 점수·평균의 중앙값 (품질 지표는 안정 쪽).

• latest_timbre_summary, latest_best_genre
    가장 최근 완료 분석 1건 (장르·음색은 현재성 반영).

• vocal_repr_embedding, f0_*, timbre_*, voiced_ratio (최신 job의 scoring_song_aligned)
    1차 추천 score_song 에 필요한 값 — song_features 와 같은 의미로 저장.
    여러 세션 집계가 아니라 가장 최근 완료 분석 1건 기준.
    워커에서 VOCAL_ANALYSIS_INCLUDE_SCORING_SONG_ALIGNED=1 이 아니면 result_data에
    scoring_song_aligned 가 없어 위 컬럼은 비어 있을 수 있음.
    이때 timbre_brightness~warmth 는 result.timbre_profile 의 value 로 fallback 채움.

• PROFILE_RANGE_OUTLIER_SEMITONES > 0 이면, 세션별 (low~high) 반음 폭이
  집단 중앙 폭 + 임계를 넘는 경우 그 세션의 lowest/highest 만 잘라 이상치 완화
  (테시투라 값은 그대로 둠).
"""
from __future__ import annotations

import math
import os
from datetime import datetime, timezone
from statistics import median
from typing import Any, Dict, List, Optional, TypedDict

from user_song_aligned_features import vocal_repr_embedding_to_pgvector_str


USER_VOCAL_PROFILES_TABLE = (os.getenv("USER_VOCAL_PROFILES_TABLE") or "user_vocal_profiles").strip()
ANALYSIS_JOBS_TABLE = (os.getenv("ANALYSIS_JOBS_TABLE") or "analysis_jobs").strip()
ANALYSIS_JOBS_ID_COLUMN = (os.getenv("ANALYSIS_JOBS_ID_COLUMN") or "id").strip()
ANALYSIS_JOBS_USER_COLUMN = (os.getenv("ANALYSIS_JOBS_USER_COLUMN") or "user_id").strip()
ANALYSIS_JOBS_STATUS_COLUMN = (os.getenv("ANALYSIS_JOBS_STATUS_COLUMN") or "status").strip()
ANALYSIS_JOBS_RESULT_COLUMN = (os.getenv("ANALYSIS_JOBS_RESULT_COLUMN") or "result_data").strip()
ANALYSIS_JOBS_TIMESTAMP_COLUMN = (
    os.getenv("ANALYSIS_JOBS_TIMESTAMP_COLUMN") or "updated_at"
).strip()

PROFILE_AGG_HISTORY_LIMIT = int(os.getenv("PROFILE_AGG_HISTORY_LIMIT") or "30")
PROFILE_RANGE_OUTLIER_SEMITONES = float(os.getenv("PROFILE_RANGE_OUTLIER_SEMITONES") or "0")

# song_features 와 동일 의미의 1차 추천용 컬럼 (user_vocal_profiles에 추가)
_SCORING_PROFILE_FLOAT_KEYS = (
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
_SCORING_PROFILE_VECTOR_KEY = "vocal_repr_embedding"


def profile_columns_from_scoring_song_aligned(aligned: Any) -> Dict[str, Any]:
    """
    scoring_song_aligned dict → user_vocal_profiles 에 쓸 컬럼 dict (pgvector 문자열 포함).

    수동 스크립트에서도 사용.
    """
    return _profile_columns_from_scoring_aligned(aligned)


def _timbre_axis_scalar(block: Any) -> Optional[float]:
    """timbre_profile 축이 {value: n} 이거나 숫자만 온 경우."""
    if isinstance(block, (int, float)) and not isinstance(block, bool):
        try:
            return float(block)
        except (TypeError, ValueError):
            return None
    if isinstance(block, dict):
        raw = block.get("value")
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None
    return None


def _timbre_scalars_from_result_timbre_profile(timbre_profile: Any) -> Dict[str, float]:
    """
    result_data.result.timbre_profile 에서 5축 raw value → DB 컬럼명.

    scoring_song_aligned 가 없을 때 timbre_brightness~warmth 만이라도 채우기 위함.
    (f0 퍼센타일·임베딩·포먼트는 scoring_song_aligned 또는 워커 기본 포함 권장)
    """
    if not isinstance(timbre_profile, dict):
        return {}
    axis_to_col = (
        ("brightness", "timbre_brightness"),
        ("roughness", "timbre_roughness"),
        ("body", "timbre_body"),
        ("clarity", "timbre_clarity"),
        ("warmth", "timbre_warmth"),
    )
    out: Dict[str, float] = {}
    for axis, col in axis_to_col:
        s = _timbre_axis_scalar(timbre_profile.get(axis))
        if s is not None:
            out[col] = s
    return out


def _profile_columns_from_scoring_aligned(aligned: Any) -> Dict[str, Any]:
    """result_data.scoring_song_aligned → user_vocal_profiles UPSERT 필드 (임베딩 없어도 스칼라는 반영)."""
    if not isinstance(aligned, dict):
        return {}
    out: Dict[str, Any] = {}
    emb = aligned.get("vocal_repr_embedding")
    if emb is not None:
        try:
            emb_list = [float(x) for x in emb]
        except (TypeError, ValueError):
            emb_list = []
        if len(emb_list) == 192:
            out[_SCORING_PROFILE_VECTOR_KEY] = vocal_repr_embedding_to_pgvector_str(emb_list)
    for k in _SCORING_PROFILE_FLOAT_KEYS:
        v = aligned.get(k)
        if v is None:
            continue
        try:
            out[k] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def _fetch_existing_scoring_columns(supabase: Any, *, user_id: str) -> Dict[str, Any]:
    cols = [_SCORING_PROFILE_VECTOR_KEY] + list(_SCORING_PROFILE_FLOAT_KEYS)
    try:
        res = (
            supabase.table(USER_VOCAL_PROFILES_TABLE)
            .select(",".join(cols))
            .eq(ANALYSIS_JOBS_USER_COLUMN, user_id)
            .limit(1)
            .execute()
        )
        row = (res.data or [None])[0]
        if not row:
            return {}
        return {k: row[k] for k in cols if row.get(k) is not None}
    except Exception:
        return {}


class _RangeSlice(TypedDict, total=False):
    lowest_hz: float
    highest_hz: float
    tessitura_low_hz: float
    tessitura_high_hz: float


def hz_to_note_label(hz: float) -> str:
    if hz is None or hz < 20.0 or (isinstance(hz, float) and math.isnan(hz)):
        return ""
    midi = 12.0 * math.log2(hz / 440.0) + 69.0
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = int(midi // 12) - 1
    note = note_names[int(midi % 12)]
    return f"{note}{octave}"


def _float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _is_success_result_data(rd: Dict[str, Any]) -> bool:
    """과거 행에 success: true/false 가 있을 수 있음. 메타는 행 컬럼만 쓰는 형식도 지원."""
    if rd.get("success") is False:
        return False
    if rd.get("error") and not rd.get("result"):
        return False
    inner = rd.get("result")
    return isinstance(inner, dict) and bool(inner.get("vocal_range"))


def _parse_vocal_range_slice(rd: Dict[str, Any]) -> Optional[_RangeSlice]:
    inner = rd.get("result") or {}
    vr = inner.get("vocal_range") or {}
    lo = _float(vr.get("lowest_hz"))
    hi = _float(vr.get("highest_hz"))
    if lo <= 0 or hi <= 0 or hi < lo:
        return None
    tl = _float(vr.get("tessitura_low_hz"), 0.0)
    th = _float(vr.get("tessitura_high_hz"), 0.0)
    if tl <= 0:
        tl = lo
    if th <= 0:
        th = hi
    if th < tl:
        tl, th = th, tl
    # 세션 내에서만 보정: 테시투라가 측정 음역 밖이면 클램프 (세션 간 min/max 확장은 하지 않음)
    tl = min(max(tl, lo), hi)
    th = min(max(th, lo), hi)
    if th < tl:
        tl, th = lo, hi
    return {
        "lowest_hz": lo,
        "highest_hz": hi,
        "tessitura_low_hz": tl,
        "tessitura_high_hz": th,
    }


def _clip_session_range_to_median(
    slices: List[_RangeSlice], max_spread_semitones: float
) -> List[_RangeSlice]:
    """세션별 (hi/lo) 반음 폭만 잘라 이상치 완화. tessitura 는 원본 유지."""
    if max_spread_semitones <= 0 or len(slices) < 3:
        return slices
    spreads: List[float] = []
    for s in slices:
        lo, hi = s["lowest_hz"], s["highest_hz"]
        if lo > 0 and hi > 0:
            spreads.append(12.0 * math.log2(hi / lo))
    if not spreads:
        return slices
    med_spread = float(median(spreads))
    out: List[_RangeSlice] = []
    for s in slices:
        lo, hi = s["lowest_hz"], s["highest_hz"]
        sp = 12.0 * math.log2(hi / lo) if lo > 0 and hi > 0 else 0.0
        if sp > med_spread + max_spread_semitones:
            center_midi = 12.0 * math.log2(math.sqrt(hi * lo) / 440.0) + 69.0
            half = med_spread / 2.0
            lo2_midi = center_midi - half
            hi2_midi = center_midi + half
            lo2 = 440.0 * (2.0 ** ((lo2_midi - 69.0) / 12.0))
            hi2 = 440.0 * (2.0 ** ((hi2_midi - 69.0) / 12.0))
            out.append(
                {
                    "lowest_hz": lo2,
                    "highest_hz": hi2,
                    "tessitura_low_hz": s["tessitura_low_hz"],
                    "tessitura_high_hz": s["tessitura_high_hz"],
                }
            )
        else:
            out.append(dict(s))
    return out


def _radar_scores(rd: Dict[str, Any]) -> Dict[str, float]:
    inner = rd.get("result") or {}
    rc = inner.get("radar_chart") or {}
    keys = (
        "pitch_stability",
        "rhythm_stability",
        "dynamic_control",
        "vocal_clarity",
        "high_note_stability",
    )
    out: Dict[str, float] = {}
    for k in keys:
        v = _float(rc.get(k), float("nan"))
        if not math.isnan(v):
            out[k] = v
    avg = _float(rc.get("average"), float("nan"))
    if not math.isnan(avg):
        out["average"] = avg
    return out


def _median_or_none(values: List[float]) -> Optional[float]:
    xs = [x for x in values if x is not None and not (isinstance(x, float) and math.isnan(x))]
    if not xs:
        return None
    return float(median(xs))


def _range_semitones(lo: float, hi: float) -> float:
    if lo <= 0 or hi <= 0 or hi < lo:
        return 0.0
    return 12.0 * math.log2(hi / lo)


def aggregate_profile_from_jobs(rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    최신순 정렬된 analysis_jobs 행 → user_vocal_profiles UPSERT payload.

    상세 정책은 모듈 상단 docstring.
    """
    if not rows:
        return None

    latest = rows[0]
    latest_id = latest.get(ANALYSIS_JOBS_ID_COLUMN) or latest.get("id")
    latest_recording = latest.get("recording_id")
    latest_rd = latest.get(ANALYSIS_JOBS_RESULT_COLUMN) or latest.get("result_data") or {}

    range_slices: List[_RangeSlice] = []
    radar_pitch: List[float] = []
    radar_rhythm: List[float] = []
    radar_high: List[float] = []
    radar_dyn: List[float] = []
    radar_clarity: List[float] = []
    radar_avg: List[float] = []

    for row in rows:
        rd = row.get(ANALYSIS_JOBS_RESULT_COLUMN) or row.get("result_data") or {}
        if not isinstance(rd, dict) or not _is_success_result_data(rd):
            continue
        sl = _parse_vocal_range_slice(rd)
        if sl:
            range_slices.append(sl)
        rs = _radar_scores(rd)
        if "pitch_stability" in rs:
            radar_pitch.append(rs["pitch_stability"])
        if "rhythm_stability" in rs:
            radar_rhythm.append(rs["rhythm_stability"])
        if "high_note_stability" in rs:
            radar_high.append(rs["high_note_stability"])
        if "dynamic_control" in rs:
            radar_dyn.append(rs["dynamic_control"])
        if "vocal_clarity" in rs:
            radar_clarity.append(rs["vocal_clarity"])
        if "average" in rs:
            radar_avg.append(rs["average"])

    if not range_slices:
        return None

    clipped = _clip_session_range_to_median(range_slices, PROFILE_RANGE_OUTLIER_SEMITONES)

    lows = [s["lowest_hz"] for s in clipped]
    highs = [s["highest_hz"] for s in clipped]
    tess_los = [s["tessitura_low_hz"] for s in clipped]
    tess_his = [s["tessitura_high_hz"] for s in clipped]

    obs_low = min(lows)
    obs_high = max(highs)
    if obs_high < obs_low:
        obs_low, obs_high = obs_high, obs_low

    stab_low = float(median(lows))
    stab_high = float(median(highs))
    if stab_high < stab_low:
        stab_low, stab_high = stab_high, stab_low

    tess_lo_med = float(median(tess_los))
    tess_hi_med = float(median(tess_his))
    if tess_hi_med < tess_lo_med:
        tess_lo_med, tess_hi_med = tess_hi_med, tess_lo_med

    inner_latest = latest_rd.get("result") if isinstance(latest_rd, dict) else {}
    gf = (inner_latest or {}).get("genre_fitness") or {}
    best_genre = gf.get("best_match")
    if best_genre is not None:
        best_genre = str(best_genre)
    tp = (inner_latest or {}).get("timbre_profile") or {}
    timbre_summary = tp.get("summary")
    if timbre_summary is not None:
        timbre_summary = str(timbre_summary)

    user_key = latest.get(ANALYSIS_JOBS_USER_COLUMN) or latest.get("user_id")
    if user_key is None:
        return None

    scoring_cols: Dict[str, Any] = {}
    if isinstance(latest_rd, dict):
        scoring_cols = _profile_columns_from_scoring_aligned(
            latest_rd.get("scoring_song_aligned")
        )
    timbre_fallback = _timbre_scalars_from_result_timbre_profile(tp)
    if timbre_fallback:
        if not scoring_cols:
            scoring_cols = dict(timbre_fallback)
        else:
            for k, v in timbre_fallback.items():
                if scoring_cols.get(k) is None:
                    scoring_cols[k] = v

    return {
        ANALYSIS_JOBS_USER_COLUMN: user_key,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "latest_analysis_job_id": latest_id,
        "latest_recording_id": latest_recording,
        "observed_lowest_hz": obs_low,
        "observed_highest_hz": obs_high,
        "observed_lowest_note": hz_to_note_label(obs_low),
        "observed_highest_note": hz_to_note_label(obs_high),
        "observed_range_semitones": round(_range_semitones(obs_low, obs_high), 4),
        "stable_lowest_hz": stab_low,
        "stable_highest_hz": stab_high,
        "stable_lowest_note": hz_to_note_label(stab_low),
        "stable_highest_note": hz_to_note_label(stab_high),
        "stable_range_semitones": round(_range_semitones(stab_low, stab_high), 4),
        "stable_tessitura_low_hz": tess_lo_med,
        "stable_tessitura_high_hz": tess_hi_med,
        "stable_tessitura_low_note": hz_to_note_label(tess_lo_med),
        "stable_tessitura_high_note": hz_to_note_label(tess_hi_med),
        "radar_median_avg": _median_or_none(radar_avg),
        "radar_median_pitch_stability": _median_or_none(radar_pitch),
        "radar_median_rhythm_stability": _median_or_none(radar_rhythm),
        "radar_median_high_note_stability": _median_or_none(radar_high),
        "radar_median_dynamic_control": _median_or_none(radar_dyn),
        "radar_median_vocal_clarity": _median_or_none(radar_clarity),
        "latest_timbre_summary": timbre_summary,
        "latest_best_genre": best_genre,
        "profile_jobs_fetched": len(rows),
        "profile_valid_range_sessions": len(clipped),
        **scoring_cols,
    }


def fetch_completed_jobs_for_user(supabase: Any, *, user_id: str) -> List[Dict[str, Any]]:
    sel = (
        f"{ANALYSIS_JOBS_ID_COLUMN}, {ANALYSIS_JOBS_USER_COLUMN}, recording_id, "
        f"{ANALYSIS_JOBS_RESULT_COLUMN}, {ANALYSIS_JOBS_TIMESTAMP_COLUMN}"
    )
    res = (
        supabase.table(ANALYSIS_JOBS_TABLE)
        .select(sel)
        .eq(ANALYSIS_JOBS_USER_COLUMN, user_id)
        .eq(ANALYSIS_JOBS_STATUS_COLUMN, "DONE")
        .order(ANALYSIS_JOBS_TIMESTAMP_COLUMN, desc=True)
        .limit(PROFILE_AGG_HISTORY_LIMIT)
        .execute()
    )
    return list(res.data or [])


def sync_user_vocal_profile_after_job(supabase: Any, *, user_id: Optional[str]) -> None:
    """
    보컬 분석 1건 DONE 직후 호출: 해당 유저 프로필 행을 전체 이력 기준으로 재계산·UPSERT.
    """
    if not user_id or not supabase:
        return
    try:
        rows = fetch_completed_jobs_for_user(supabase, user_id=user_id)
        payload = aggregate_profile_from_jobs(rows)
        if not payload:
            print("⚠️  user_vocal_profiles 갱신 스킵: 집계 가능한 완료 분석이 없습니다.")
            return
        if _SCORING_PROFILE_VECTOR_KEY not in payload:
            prev_scoring = _fetch_existing_scoring_columns(supabase, user_id=user_id)
            payload.update(prev_scoring)
        supabase.table(USER_VOCAL_PROFILES_TABLE).upsert(
            payload,
            on_conflict=ANALYSIS_JOBS_USER_COLUMN,
        ).execute()
        print(
            f"✓ user_vocal_profiles 갱신 완료 (user={user_id}, "
            f"valid_range_sessions={payload.get('profile_valid_range_sessions')})"
        )
    except Exception as e:
        print(f"⚠️  user_vocal_profiles 갱신 실패 (분석 저장은 유지): {e}")

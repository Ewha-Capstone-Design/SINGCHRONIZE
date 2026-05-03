"""
F0 프레임 → 음별 커브(v1): 빈도(70%) + 테시투라 prior(30%), 스무딩 후 0~100 정규화.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import librosa
import numpy as np

FREQ_WEIGHT = 0.7
PRIOR_WEIGHT = 0.3
TESS_PRIOR_DECAY = 0.12
COMFORT_SCORE_THRESHOLD = 70.0


def _midi_to_note_label(midi_int: int) -> str:
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    mf = float(midi_int)
    if mf < 0 or np.isnan(mf):
        return "N/A"
    octave = int(mf // 12) - 1
    note = note_names[int(mf % 12)]
    return f"{note}{octave}"


def _hz_to_midi_int(hz: float) -> Optional[int]:
    if hz is None or hz < 20.0 or np.isnan(hz):
        return None
    return int(round(float(librosa.hz_to_midi(hz))))


def _tessitura_midi_bounds(
    tess_low_hz: float, tess_high_hz: float, fallback_lo: int, fallback_hi: int
) -> Tuple[int, int]:
    lo = _hz_to_midi_int(float(tess_low_hz))
    hi = _hz_to_midi_int(float(tess_high_hz))
    if lo is None or hi is None:
        return fallback_lo, fallback_hi
    if lo > hi:
        lo, hi = hi, lo
    return lo, hi


def _prior_for_midi(m: int, tess_lo: int, tess_hi: int) -> float:
    if tess_lo <= m <= tess_hi:
        return 1.0
    if m < tess_lo:
        dist = float(tess_lo - m)
    else:
        dist = float(m - tess_hi)
    return max(0.0, 1.0 - TESS_PRIOR_DECAY * dist)


def _smooth_1d(raw: np.ndarray) -> np.ndarray:
    n = len(raw)
    if n == 0:
        return raw
    if n == 1:
        return raw.copy()
    if n == 2:
        return np.array(
            [0.75 * raw[0] + 0.25 * raw[1], 0.25 * raw[0] + 0.75 * raw[1]],
            dtype=np.float64,
        )
    out = np.zeros(n, dtype=np.float64)
    out[0] = 0.75 * raw[0] + 0.25 * raw[1]
    out[-1] = 0.25 * raw[-2] + 0.75 * raw[-1]
    for i in range(1, n - 1):
        out[i] = 0.25 * raw[i - 1] + 0.5 * raw[i] + 0.25 * raw[i + 1]
    return out


def _normalize_0_100(smooth: np.ndarray) -> np.ndarray:
    mn = float(np.min(smooth))
    mx = float(np.max(smooth))
    if mx > mn:
        return np.clip(100.0 * (smooth - mn) / (mx - mn), 0.0, 100.0)
    return np.full_like(smooth, 100.0, dtype=np.float64)


def _pick_comfortable_run(
    notes: List[str], scores: List[float], peak_idx: int, threshold: float
) -> Optional[Tuple[int, int]]:
    """score >= threshold 인 최장 연속 구간 (동률이면 peak_idx 포함 구간 우선). inclusive indices."""
    n = len(scores)
    if n == 0:
        return None
    runs: List[Tuple[int, int]] = []
    i = 0
    while i < n:
        if scores[i] >= threshold:
            j = i
            while j < n and scores[j] >= threshold:
                j += 1
            runs.append((i, j - 1))
            i = j
        else:
            i += 1
    if not runs:
        return None
    best_len = max(b - a + 1 for a, b in runs)
    candidates = [(a, b) for a, b in runs if b - a + 1 == best_len]
    for a, b in candidates:
        if a <= peak_idx <= b:
            return a, b
    return candidates[0]


def compute_vocal_range_curve(pitch_features: Dict) -> Dict:
    """
    voiced 프레임 F0를 반음 bin에 넣어 histogram → frequency,
    tessitura 구간 기반 prior → 가중 합 → 스무딩 → 0~100.

    pitch_features: extract_pitch() 결과 (f0_contour, voiced_mask, tessitura_*_hz).
    """
    f0_full = np.asarray(pitch_features.get("f0_contour"), dtype=np.float64)
    voiced = np.asarray(pitch_features.get("voiced_mask"), dtype=bool)
    if f0_full.size == 0 or voiced.size == 0 or f0_full.shape != voiced.shape:
        return _empty_curve(pitch_features)

    valid = voiced & (f0_full > 1e-6)
    f0_voiced = f0_full[valid]
    total = int(f0_voiced.size)
    if total == 0:
        return _empty_curve(pitch_features)

    midi = 69.0 + 12.0 * np.log2(f0_voiced / 440.0)
    note_bins = np.rint(midi).astype(np.int32)
    note_bins = note_bins[np.isfinite(midi)]
    if note_bins.size == 0:
        return _empty_curve(pitch_features)

    lo_bin = int(np.min(note_bins))
    hi_bin = int(np.max(note_bins))
    if lo_bin > hi_bin:
        lo_bin, hi_bin = hi_bin, lo_bin

    tess_lo_hz = float(pitch_features.get("tessitura_low") or 0.0)
    tess_hi_hz = float(pitch_features.get("tessitura_high") or 0.0)
    tess_lo_m, tess_hi_m = _tessitura_midi_bounds(tess_lo_hz, tess_hi_hz, lo_bin, hi_bin)

    counts = np.bincount(note_bins - lo_bin, minlength=hi_bin - lo_bin + 1)
    midi_indices = np.arange(lo_bin, hi_bin + 1, dtype=np.int32)

    freq = counts.astype(np.float64) / float(total)
    priors = np.array(
        [_prior_for_midi(int(m), tess_lo_m, tess_hi_m) for m in midi_indices],
        dtype=np.float64,
    )
    raw = FREQ_WEIGHT * freq + PRIOR_WEIGHT * priors
    smooth = _smooth_1d(raw)
    score100 = _normalize_0_100(smooth)
    notes_list = [_midi_to_note_label(int(m)) for m in midi_indices]

    peak_idx = int(np.argmax(score100))
    peak_note = notes_list[peak_idx] if notes_list else "N/A"

    run = _pick_comfortable_run(
        notes_list, [float(s) for s in score100], peak_idx, COMFORT_SCORE_THRESHOLD
    )
    scores_list = [int(round(float(np.clip(s, 0.0, 100.0)))) for s in score100]
    if run is not None:
        a, b = run
        comfortable_range = {"low_note": notes_list[a], "high_note": notes_list[b]}
    else:
        # 70점 이상 구간 없음 → 테시투라 음이름(요약)으로 폴백
        comfortable_range = {
            "low_note": _midi_to_note_label(tess_lo_m),
            "high_note": _midi_to_note_label(tess_hi_m),
        }

    return {
        "notes": notes_list,
        "scores": scores_list,
        "comfortable_range": comfortable_range,
        "peak_note": peak_note,
    }


def _empty_curve(pitch_features: Dict) -> Dict:
    tess_lo_hz = float(pitch_features.get("tessitura_low") or 0.0)
    tess_hi_hz = float(pitch_features.get("tessitura_high") or 0.0)
    tl = _hz_to_midi_int(tess_lo_hz)
    th = _hz_to_midi_int(tess_hi_hz)
    if tl is not None and th is not None and tl > th:
        tl, th = th, tl
    low_n = _midi_to_note_label(tl) if tl is not None else "N/A"
    high_n = _midi_to_note_label(th) if th is not None else "N/A"
    return {
        "notes": [],
        "scores": [],
        "comfortable_range": {"low_note": low_n, "high_note": high_n},
        "peak_note": "N/A",
    }

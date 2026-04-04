from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.db.repository import (
    get_all_user_embeddings,
    get_neighbor_interactions,
    get_song_embedding,
    get_user_embedding,
    get_user_excluded_songs,
)

COMPATIBILITY_WEIGHT = float(os.getenv("STAGE3_COMPATIBILITY_WEIGHT") or "0.2")
MIN_COMPATIBILITY = float(os.getenv("STAGE3_MIN_COMPATIBILITY") or "0.3")
DEFAULT_TOP_K = int(os.getenv("STAGE3_NEIGHBOR_TOP_K") or "30")


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def get_neighbors(
    user_id: str,
    me: np.ndarray,
    top_k: int = DEFAULT_TOP_K,
) -> List[Tuple[str, float]]:
    all_users = get_all_user_embeddings()
    sims: List[Tuple[str, float]] = []
    for u in all_users:
        uid = u["user_id"]
        if uid == user_id:
            continue
        emb = u["embedding"]
        sims.append((uid, cosine_similarity(me, emb)))
    sims.sort(key=lambda x: x[1], reverse=True)
    return sims[:top_k]


def recommend_similar_voice(
    user_id: str,
    period: str,
    limit: int = 10,
    interaction_since: Optional[datetime] = None,
    interaction_until: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    me = get_user_embedding(user_id)
    if me is None:
        return []

    neighbors = get_neighbors(user_id, me)
    if not neighbors:
        return []

    interactions = get_neighbor_interactions(
        [u[0] for u in neighbors],
        period,
        interaction_since=interaction_since,
        interaction_until=interaction_until,
    )
    neighbor_map = {uid: sim for uid, sim in neighbors}

    song_scores: defaultdict[str, float] = defaultdict(float)
    for row in interactions:
        uid = row["user_id"]
        song_id = row["song_id"]
        weight = float(row.get("weight") or 1.0)
        sim = neighbor_map.get(uid, 0.0)
        song_scores[song_id] += sim * weight

    excluded = get_user_excluded_songs(user_id)

    results: List[Dict[str, Any]] = []
    for song_id, score in song_scores.items():
        if song_id in excluded:
            continue
        s_emb = get_song_embedding(song_id)
        compatibility = cosine_similarity(me, s_emb) if s_emb is not None else 0.0
        if compatibility < MIN_COMPATIBILITY:
            continue
        final_score = score + COMPATIBILITY_WEIGHT * compatibility
        results.append({"song_id": song_id, "score": final_score})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

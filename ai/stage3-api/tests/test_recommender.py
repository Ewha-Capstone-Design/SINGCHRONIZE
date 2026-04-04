"""
stage3 협업 필터링 로직 검증 (DB 없이 mock).

실행: cd ai/stage3-api && python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && .venv/bin/pytest tests/ -v
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import numpy as np
import pytest

from app.service import recommender as rec


def _unit(d: int, i: int) -> np.ndarray:
    v = np.zeros(d, dtype=np.float64)
    v[i] = 1.0
    return v


def test_cosine_similarity_basic():
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([1.0, 0.0, 0.0])
    c = np.array([0.0, 1.0, 0.0])
    assert rec.cosine_similarity(a, b) == pytest.approx(1.0)
    assert rec.cosine_similarity(a, c) == pytest.approx(0.0)


def test_cosine_similarity_zero_norm():
    z = np.zeros(3)
    assert rec.cosine_similarity(z, np.array([1.0, 0.0, 0.0])) == 0.0


def test_get_neighbors_orders_by_similarity(monkeypatch):
    me = _unit(4, 0)
    rows = [
        {"user_id": "self", "embedding": me},
        {"user_id": "close", "embedding": _unit(4, 0)},
        {"user_id": "mid", "embedding": np.array([1.0, 1.0, 0.0, 0.0])},
        {"user_id": "far", "embedding": _unit(4, 3)},
    ]

    def fake_all():
        return rows

    monkeypatch.setattr(rec, "get_all_user_embeddings", fake_all)
    n = rec.get_neighbors("self", me, top_k=2)
    assert [x[0] for x in n] == ["close", "mid"]
    assert n[0][1] >= n[1][1]


@patch("app.service.recommender.get_song_embedding")
@patch("app.service.recommender.get_user_excluded_songs")
@patch("app.service.recommender.get_neighbor_interactions")
@patch("app.service.recommender.get_neighbors")
@patch("app.service.recommender.get_user_embedding")
def test_recommend_collaborative_score_orders(
    mock_me,
    mock_neighbors,
    mock_inter,
    mock_excl,
    mock_song_emb,
):
    """이웃 유사도가 클수록 같은 위시 곡에 가산되는지."""
    dim = 8
    uvec = _unit(dim, 0)
    mock_me.return_value = uvec
    mock_neighbors.return_value = [("n_high", 1.0), ("n_low", 0.25)]
    mock_inter.return_value = [
        {"user_id": "n_high", "song_id": "song_a", "weight": 1.0},
        {"user_id": "n_low", "song_id": "song_b", "weight": 1.0},
    ]
    mock_excl.return_value = set()

    def song_emb(sid: str):
        return uvec.copy()

    mock_song_emb.side_effect = song_emb

    out = rec.recommend_similar_voice("u1", "week", limit=10)
    ids = [x["song_id"] for x in out]
    assert ids == ["song_a", "song_b"]
    assert out[0]["score"] > out[1]["score"]


@patch("app.service.recommender.get_song_embedding")
@patch("app.service.recommender.get_user_excluded_songs")
@patch("app.service.recommender.get_neighbor_interactions")
@patch("app.service.recommender.get_neighbors")
@patch("app.service.recommender.get_user_embedding")
def test_recommend_drops_below_min_compatibility(
    mock_me,
    mock_neighbors,
    mock_inter,
    mock_excl,
    mock_song_emb,
):
    dim = 8
    uvec = _unit(dim, 0)
    mock_me.return_value = uvec
    mock_neighbors.return_value = [("n1", 1.0)]
    mock_inter.return_value = [{"user_id": "n1", "song_id": "bad_song", "weight": 5.0}]
    mock_excl.return_value = set()
    mock_song_emb.return_value = _unit(dim, 1)

    out = rec.recommend_similar_voice("u1", "week", limit=10)
    assert out == []


@patch("app.service.recommender.get_song_embedding")
@patch("app.service.recommender.get_user_excluded_songs")
@patch("app.service.recommender.get_neighbor_interactions")
@patch("app.service.recommender.get_neighbors")
@patch("app.service.recommender.get_user_embedding")
def test_recommend_respects_excluded(
    mock_me,
    mock_neighbors,
    mock_inter,
    mock_excl,
    mock_song_emb,
):
    dim = 4
    uvec = _unit(dim, 0)
    mock_me.return_value = uvec
    mock_neighbors.return_value = [("n1", 1.0)]
    mock_inter.return_value = [{"user_id": "n1", "song_id": "x", "weight": 1.0}]
    mock_excl.return_value = {"x"}
    mock_song_emb.return_value = uvec.copy()

    assert rec.recommend_similar_voice("u1", "week") == []


@patch("app.service.recommender.get_neighbors")
@patch("app.service.recommender.get_user_embedding")
def test_recommend_empty_when_no_profile(mock_me, mock_neighbors):
    mock_me.return_value = None
    assert rec.recommend_similar_voice("u1", "week") == []
    mock_neighbors.assert_not_called()


@patch("app.service.recommender.get_song_embedding")
@patch("app.service.recommender.get_user_excluded_songs")
@patch("app.service.recommender.get_neighbor_interactions")
@patch("app.service.recommender.get_neighbors")
@patch("app.service.recommender.get_user_embedding")
def test_recommend_passes_time_window_to_repository(
    mock_me, mock_neighbors, mock_inter, mock_excl, _mock_song,
):
    mock_me.return_value = _unit(4, 0)
    mock_neighbors.return_value = [("n1", 1.0)]
    mock_inter.return_value = []
    mock_excl.return_value = set()

    since = datetime(2026, 1, 1, tzinfo=timezone.utc)
    until = datetime(2026, 1, 15, tzinfo=timezone.utc)
    rec.recommend_similar_voice(
        "u1",
        "week",
        interaction_since=since,
        interaction_until=until,
    )
    mock_inter.assert_called_once()
    _, kwargs = mock_inter.call_args
    assert kwargs["interaction_since"] is since
    assert kwargs["interaction_until"] is until

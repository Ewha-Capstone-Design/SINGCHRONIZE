import numpy as np
from unittest.mock import patch

from app.service.recommender import cosine_similarity, recommend_similar_voice


def test_cosine_orthogonal():
    a = np.array([1.0, 0.0], dtype=np.float64)
    b = np.array([0.0, 1.0], dtype=np.float64)
    assert abs(cosine_similarity(a, b)) < 1e-9


def test_cosine_parallel():
    a = np.array([3.0, 4.0], dtype=np.float64)
    b = np.array([6.0, 8.0], dtype=np.float64)
    assert abs(cosine_similarity(a, b) - 1.0) < 1e-9


def test_recommend_empty_when_no_profile():
    with patch("app.service.recommender.get_user_embedding", return_value=None):
        out = recommend_similar_voice("user-1", "week", limit=5)
    assert out == []


@patch("app.service.recommender.get_song_embedding")
@patch("app.service.recommender.get_user_excluded_songs")
@patch("app.service.recommender.get_neighbor_interactions")
@patch("app.service.recommender.get_all_user_embeddings")
@patch("app.service.recommender.get_user_embedding")
def test_recommend_combines_neighbor_wish_and_compatibility(
    mock_me,
    mock_all,
    mock_inter,
    mock_excl,
    mock_song_emb,
):
    me = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    neighbor_emb = np.array([1.0, 0.0, 0.0], dtype=np.float64)

    mock_me.return_value = me
    mock_all.return_value = [
        {"user_id": "user-1", "embedding": me},
        {"user_id": "n1", "embedding": neighbor_emb},
    ]
    mock_inter.return_value = [{"user_id": "n1", "song_id": "song-a", "weight": 1.0}]
    mock_excl.return_value = set()
    mock_song_emb.return_value = np.array([1.0, 0.0, 0.0], dtype=np.float64)

    with patch.multiple(
        "app.service.recommender",
        COMPATIBILITY_WEIGHT=0.2,
        MIN_COMPATIBILITY=0.3,
        DEFAULT_TOP_K=10,
    ):
        out = recommend_similar_voice("user-1", "week", limit=10)

    assert len(out) == 1
    assert out[0]["song_id"] == "song-a"
    # 협업 1.0 * 이웃유사도 1.0 + 0.2 * 호환도 1.0
    assert abs(out[0]["score"] - 1.2) < 1e-6


@patch("app.service.recommender.get_song_embedding")
@patch("app.service.recommender.get_user_excluded_songs")
@patch("app.service.recommender.get_neighbor_interactions")
@patch("app.service.recommender.get_all_user_embeddings")
@patch("app.service.recommender.get_user_embedding")
def test_recommend_respects_excluded_songs(
    mock_me,
    mock_all,
    mock_inter,
    mock_excl,
    mock_song_emb,
):
    me = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    mock_me.return_value = me
    mock_all.return_value = [
        {"user_id": "u", "embedding": me},
        {"user_id": "n1", "embedding": me.copy()},
    ]
    mock_inter.return_value = [{"user_id": "n1", "song_id": "x", "weight": 1.0}]
    mock_excl.return_value = {"x"}
    mock_song_emb.return_value = me

    out = recommend_similar_voice("u", "week")
    assert out == []

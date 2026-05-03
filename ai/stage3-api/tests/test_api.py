from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@patch("app.main.recommend_similar_voice")
def test_similar_voice_picks_ok(mock_rec):
    mock_rec.return_value = [{"song_id": "s1", "score": 1.5}]
    r = client.post(
        "/stage3/similar-voice-picks",
        json={"user_id": "550e8400-e29b-41d4-a716-446655440000", "period": "week", "limit": 5},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["results"] == [{"song_id": "s1", "score": 1.5}]
    assert body.get("meta") is None


def test_similar_voice_picks_validation_until_before_since():
    r = client.post(
        "/stage3/similar-voice-picks",
        json={
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "period": "week",
            "interaction_since": "2024-06-01T00:00:00Z",
            "interaction_until": "2024-05-01T00:00:00Z",
        },
    )
    assert r.status_code == 422


@patch("app.main.recommend_similar_voice", side_effect=RuntimeError("no supabase"))
def test_similar_voice_picks_503_on_runtime_error(mock_rec):
    r = client.post(
        "/stage3/similar-voice-picks",
        json={"user_id": "550e8400-e29b-41d4-a716-446655440000", "period": "week"},
    )
    assert r.status_code == 503

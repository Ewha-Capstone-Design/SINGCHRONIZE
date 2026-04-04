from datetime import datetime, timedelta, timezone

import pytest

from app.db import repository as repo


def test_resolve_interaction_window_explicit_overrides():
    since = datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc)
    until = datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc)
    a, b = repo.resolve_interaction_window("week", since, until)
    assert a == since
    assert b == until


def test_resolve_interaction_window_naive_is_utc():
    naive = datetime(2026, 3, 1, 0, 0, 0)
    a, _b = repo.resolve_interaction_window("week", naive, None)
    assert a.tzinfo == timezone.utc


def test_resolve_interaction_invalid_order_raises():
    from pydantic import ValidationError

    from app.models import RecommendRequest

    with pytest.raises(ValidationError):
        RecommendRequest(
            user_id="x",
            interaction_since=datetime(2026, 1, 10, tzinfo=timezone.utc),
            interaction_until=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

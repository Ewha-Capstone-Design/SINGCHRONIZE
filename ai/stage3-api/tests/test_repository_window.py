"""기간·명시적 since/until 윈도우 계산 단위 테스트."""

import datetime as dt
from unittest.mock import patch

from app.db.repository import interaction_window_from_period, resolve_interaction_window


def test_resolve_prefers_explicit_since_until_over_period():
    since = dt.datetime(2024, 1, 1, 10, 0, tzinfo=dt.timezone.utc)
    until = dt.datetime(2024, 1, 31, 23, 0, tzinfo=dt.timezone.utc)
    s, u = resolve_interaction_window("week", since, until)
    assert s == since
    assert u == until


@patch("app.db.repository.datetime")
def test_week_window_seven_days(mock_datetime):
    fixed = dt.datetime(2024, 6, 15, 12, 0, 0, tzinfo=dt.timezone.utc)
    mock_datetime.now.return_value = fixed
    since, until = interaction_window_from_period("week")
    assert until == fixed
    assert since == fixed - dt.timedelta(days=7)


@patch("app.db.repository.datetime")
def test_month_window_thirty_days(mock_datetime):
    fixed = dt.datetime(2024, 3, 1, 0, 0, 0, tzinfo=dt.timezone.utc)
    mock_datetime.now.return_value = fixed
    since, until = interaction_window_from_period("month")
    assert until == fixed
    assert since == fixed - dt.timedelta(days=30)


@patch("app.db.repository.CALENDAR_TZ", "UTC")
@patch("app.db.repository.datetime")
def test_today_starts_calendar_midnight_utc(mock_datetime):
    fixed = dt.datetime(2024, 7, 10, 15, 30, 0, tzinfo=dt.timezone.utc)
    mock_datetime.now.return_value = fixed
    since, until = interaction_window_from_period("today")
    assert until == fixed
    assert since == dt.datetime(2024, 7, 10, 0, 0, 0, tzinfo=dt.timezone.utc)

"""Unit tests for Bookmark and HistoryItem models."""

from __future__ import annotations

from datetime import UTC, datetime

from pybrowser.models.bookmark import Bookmark
from pybrowser.models.history_item import HistoryItem


def test_bookmark_to_dict_and_from_row() -> None:
    now = datetime.now(UTC)
    bm = Bookmark(
        id=42,
        url="https://docs.python.org",
        title="Python Documentation",
        folder="dev",
        created_at=now,
    )

    data = bm.to_dict()
    assert data["id"] == 42
    assert data["url"] == "https://docs.python.org"
    assert data["title"] == "Python Documentation"
    assert data["folder"] == "dev"
    assert data["created_at"] == now.isoformat()

    row = (42, "https://docs.python.org", "Python Documentation", "dev", now.isoformat())
    hydrated = Bookmark.from_row(row)
    assert hydrated.id == 42
    assert hydrated.url == bm.url
    assert hydrated.title == bm.title


def test_history_item_to_dict_and_from_row() -> None:
    now = datetime.now(UTC)
    item = HistoryItem(
        id=7,
        url="https://news.ycombinator.com",
        title="Hacker News",
        visited_at=now,
        visit_count=5,
    )

    data = item.to_dict()
    assert data["id"] == 7
    assert data["url"] == "https://news.ycombinator.com"
    assert data["visit_count"] == 5

    row = (7, "https://news.ycombinator.com", "Hacker News", now.isoformat(), 5)
    hydrated = HistoryItem.from_row(row)
    assert hydrated.id == 7
    assert hydrated.visit_count == 5

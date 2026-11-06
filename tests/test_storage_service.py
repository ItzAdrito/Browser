"""Unit tests for StorageService repository operations."""

from __future__ import annotations

from pybrowser.services.storage_service import StorageService


def test_history_record_and_fetch(temp_storage: StorageService) -> None:
    temp_storage.record_visit("https://example.com", "Example Domain")
    temp_storage.record_visit("https://python.org", "Python Language")

    history = temp_storage.get_history()
    assert len(history) == 2
    assert history[0].url == "https://python.org"
    assert history[0].visit_count == 1


def test_history_duplicate_increments_count(temp_storage: StorageService) -> None:
    temp_storage.record_visit("https://example.com", "Example")
    temp_storage.record_visit("https://example.com", "Example New Title")

    history = temp_storage.get_history()
    assert len(history) == 1
    assert history[0].visit_count == 2
    assert history[0].title == "Example New Title"


def test_history_search(temp_storage: StorageService) -> None:
    temp_storage.record_visit("https://github.com", "GitHub")
    temp_storage.record_visit("https://gitlab.com", "GitLab")
    temp_storage.record_visit("https://google.com", "Google")

    results = temp_storage.get_history(search="Git")
    assert len(results) == 2


def test_history_delete_and_clear(temp_storage: StorageService) -> None:
    temp_storage.record_visit("https://example.com", "Example")
    temp_storage.record_visit("https://test.com", "Test")

    history = temp_storage.get_history()
    assert len(history) == 2

    # Delete single item
    item_id = history[0].id
    assert item_id is not None
    temp_storage.delete_history_item(item_id)

    remaining = temp_storage.get_history()
    assert len(remaining) == 1

    # Clear all
    temp_storage.clear_history()
    assert len(temp_storage.get_history()) == 0


def test_bookmark_add_and_query(temp_storage: StorageService) -> None:
    assert temp_storage.is_bookmarked("https://python.org") is False

    bm = temp_storage.add_bookmark("https://python.org", "Python Official Site")
    assert bm.url == "https://python.org"
    assert bm.title == "Python Official Site"
    assert temp_storage.is_bookmarked("https://python.org") is True

    bookmarks = temp_storage.get_bookmarks()
    assert len(bookmarks) == 1
    assert bookmarks[0].url == "https://python.org"


def test_bookmark_upsert(temp_storage: StorageService) -> None:
    temp_storage.add_bookmark("https://example.com", "Old Title")
    temp_storage.add_bookmark("https://example.com", "Updated Title")

    bookmarks = temp_storage.get_bookmarks()
    assert len(bookmarks) == 1
    assert bookmarks[0].title == "Updated Title"


def test_bookmark_remove(temp_storage: StorageService) -> None:
    temp_storage.add_bookmark("https://example.com", "Example")
    assert temp_storage.is_bookmarked("https://example.com") is True

    removed = temp_storage.remove_bookmark("https://example.com")
    assert removed is True
    assert temp_storage.is_bookmarked("https://example.com") is False

    # Second removal returns False
    assert temp_storage.remove_bookmark("https://example.com") is False

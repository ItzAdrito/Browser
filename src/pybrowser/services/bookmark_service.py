"""Bookmark service providing high-level business logic for bookmark management."""

from __future__ import annotations

from pybrowser.core.logger import get_logger
from pybrowser.models.bookmark import Bookmark
from pybrowser.services.storage_service import StorageService

logger = get_logger(__name__)


class BookmarkService:
    """Service layer managing bookmarks."""

    def __init__(self, storage: StorageService) -> None:
        self._storage = storage

    def toggle_bookmark(self, url: str, title: str) -> bool:
        """Toggle bookmark state: adds if not present, removes if already present.

        Returns:
            True if now bookmarked, False if removed.
        """
        if self._storage.is_bookmarked(url):
            self._storage.remove_bookmark(url)
            logger.info("Removed bookmark: %s", url)
            return False
        else:
            self._storage.add_bookmark(url, title)
            logger.info("Added bookmark: %s ('%s')", url, title)
            return True

    def is_bookmarked(self, url: str) -> bool:
        """Check if URL is bookmarked."""
        return self._storage.is_bookmarked(url)

    def list_bookmarks(self, search: str | None = None) -> list[Bookmark]:
        """List bookmarks optionally filtered by search text."""
        return self._storage.get_bookmarks(search)

    def remove_bookmark(self, url: str) -> bool:
        """Remove bookmark by URL."""
        return self._storage.remove_bookmark(url)

"""History service providing high-level business logic for browsing history."""

from __future__ import annotations

from pybrowser.core.logger import get_logger
from pybrowser.models.history_item import HistoryItem
from pybrowser.services.storage_service import StorageService

logger = get_logger(__name__)


class HistoryService:
    """Service layer managing browsing history."""

    def __init__(self, storage: StorageService) -> None:
        self._storage = storage

    def log_visit(self, url: str, title: str) -> None:
        """Record a newly visited page."""
        try:
            self._storage.record_visit(url, title)
            logger.debug("Logged visit for: %s", url)
        except Exception as exc:
            logger.warning("Failed to record history for %s: %s", url, exc)

    def fetch_history(self, limit: int = 150, search: str | None = None) -> list[HistoryItem]:
        """Retrieve recent history entries."""
        return self._storage.get_history(limit=limit, search=search)

    def delete_entry(self, entry_id: int) -> None:
        """Remove a single history entry."""
        self._storage.delete_history_item(entry_id)

    def clear_all(self) -> None:
        """Wipe entire history database."""
        self._storage.clear_history()
        logger.info("Browsing history wiped")

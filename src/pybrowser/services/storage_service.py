"""SQLite Storage Service implementing the Repository Pattern for persistence."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from pybrowser.core.exceptions import StorageError
from pybrowser.core.logger import get_logger
from pybrowser.models.bookmark import Bookmark
from pybrowser.models.history_item import HistoryItem

logger = get_logger(__name__)


class StorageService:
    """Thread-safe SQLite storage repository for history and bookmarks."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the storage service and run schema migrations.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._init_database()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for obtaining a database connection with auto-commit."""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode = WAL;")  # Write-Ahead Logging for high concurrency
            conn.execute("PRAGMA foreign_keys = ON;")
            yield conn
            conn.commit()
        except sqlite3.Error as exc:
            logger.error("Database transaction failed: %s", exc, exc_info=True)
            raise StorageError("Database transaction failed", details=str(exc)) from exc
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Create tables and performance indexes if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    visited_at TEXT NOT NULL,
                    visit_count INTEGER NOT NULL DEFAULT 1
                );
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_visited_at ON history(visited_at DESC);"
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_url ON history(url);")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    folder TEXT NOT NULL DEFAULT 'default',
                    created_at TEXT NOT NULL
                );
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_url ON bookmarks(url);")
            logger.debug("Database initialized at %s", self.db_path)

    # ---------------------------------------------------------
    # History Operations
    # ---------------------------------------------------------
    def record_visit(self, url: str, title: str) -> None:
        """Record or update page visit in history.

        Args:
            url: Visited page URL.
            title: Title of the visited page.
        """
        if not url or url.startswith("about:"):
            return

        now_iso = datetime.now(UTC).isoformat()
        clean_title = title.strip() or url

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check if this URL was visited recently
            cursor.execute(
                "SELECT id, visit_count FROM history WHERE url = ? ORDER BY id DESC LIMIT 1;",
                (url,),
            )
            existing = cursor.fetchone()
            if existing:
                row_id, count = existing
                cursor.execute(
                    """
                    UPDATE history
                    SET title = ?, visited_at = ?, visit_count = ?
                    WHERE id = ?;
                    """,
                    (clean_title, now_iso, count + 1, row_id),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO history (url, title, visited_at, visit_count)
                    VALUES (?, ?, ?, 1);
                    """,
                    (url, clean_title, now_iso),
                )

    def get_history(self, limit: int = 200, search: str | None = None) -> list[HistoryItem]:
        """Fetch browsing history records in descending chronological order.

        Args:
            limit: Maximum number of rows to return.
            search: Optional substring filter for URL or title.

        Returns:
            List of HistoryItem instances.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if search and search.strip():
                query_filter = f"%{search.strip()}%"
                cursor.execute(
                    """
                    SELECT id, url, title, visited_at, visit_count
                    FROM history
                    WHERE url LIKE ? OR title LIKE ?
                    ORDER BY visited_at DESC
                    LIMIT ?;
                    """,
                    (query_filter, query_filter, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, url, title, visited_at, visit_count
                    FROM history
                    ORDER BY visited_at DESC
                    LIMIT ?;
                    """,
                    (limit,),
                )
            rows = cursor.fetchall()
            return [HistoryItem.from_row(row) for row in rows]

    def delete_history_item(self, item_id: int) -> None:
        """Delete a single history entry by ID."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM history WHERE id = ?;", (item_id,))

    def clear_history(self) -> None:
        """Purge all browsing history records."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM history;")

    # ---------------------------------------------------------
    # Bookmark Operations
    # ---------------------------------------------------------
    def add_bookmark(self, url: str, title: str, folder: str = "default") -> Bookmark:
        """Add or update a bookmark.

        Args:
            url: Unique target URL.
            title: Display title for the bookmark.
            folder: Category or folder name.

        Returns:
            Created or updated Bookmark instance.
        """
        if not url:
            raise ValueError("URL cannot be empty")

        now_iso = datetime.now(UTC).isoformat()
        clean_title = title.strip() or url

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO bookmarks (url, title, folder, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    folder = excluded.folder;
                """,
                (url, clean_title, folder, now_iso),
            )
            bookmark_id = cursor.lastrowid or 0
            return Bookmark(
                id=bookmark_id,
                url=url,
                title=clean_title,
                folder=folder,
                created_at=datetime.fromisoformat(now_iso),
            )

    def remove_bookmark(self, url: str) -> bool:
        """Delete bookmark by URL.

        Returns:
            True if a record was deleted, False otherwise.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bookmarks WHERE url = ?;", (url,))
            return cursor.rowcount > 0

    def is_bookmarked(self, url: str) -> bool:
        """Check if a URL is currently bookmarked."""
        if not url:
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM bookmarks WHERE url = ? LIMIT 1;", (url,))
            return cursor.fetchone() is not None

    def get_bookmarks(self, search: str | None = None) -> list[Bookmark]:
        """Fetch all saved bookmarks.

        Args:
            search: Optional filter string for URL or title.

        Returns:
            List of Bookmark instances.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if search and search.strip():
                query_filter = f"%{search.strip()}%"
                cursor.execute(
                    """
                    SELECT id, url, title, folder, created_at
                    FROM bookmarks
                    WHERE url LIKE ? OR title LIKE ?
                    ORDER BY title ASC;
                    """,
                    (query_filter, query_filter),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, url, title, folder, created_at
                    FROM bookmarks
                    ORDER BY title ASC;
                    """
                )
            rows = cursor.fetchall()
            return [Bookmark.from_row(row) for row in rows]

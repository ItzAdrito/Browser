"""Bookmark domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class Bookmark:
    """Represents a saved bookmark entry."""

    url: str
    title: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    folder: str = "default"
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert bookmark entity to JSON-serializable dictionary."""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "folder": self.folder,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_row(cls, row: tuple[Any, ...]) -> Bookmark:
        """Hydrate entity from SQLite query row: (id, url, title, folder, created_at)."""
        created_at = (
            datetime.fromisoformat(row[4]) if isinstance(row[4], str) else datetime.now(UTC)
        )
        return cls(
            id=row[0],
            url=row[1],
            title=row[2],
            folder=row[3],
            created_at=created_at,
        )

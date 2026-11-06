"""History item domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class HistoryItem:
    """Represents a visited web page history record."""

    url: str
    title: str
    visited_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    visit_count: int = 1
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert history entity to JSON-serializable dictionary."""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "visited_at": self.visited_at.isoformat(),
            "visit_count": self.visit_count,
        }

    @classmethod
    def from_row(cls, row: tuple[Any, ...]) -> HistoryItem:
        """Hydrate entity from SQLite query row: (id, url, title, visited_at, visit_count)."""
        visited_at = (
            datetime.fromisoformat(row[3]) if isinstance(row[3], str) else datetime.now(UTC)
        )
        return cls(
            id=row[0],
            url=row[1],
            title=row[2],
            visited_at=visited_at,
            visit_count=row[4],
        )

"""Pytest fixtures and test harnesses."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure src/ is on sys.path for testing
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from pybrowser.services.storage_service import StorageService  # noqa: E402


@pytest.fixture
def temp_storage(tmp_path: Path) -> StorageService:
    """Provide an isolated, temporary SQLite storage service."""
    db_file = tmp_path / "test_browser.db"
    return StorageService(db_file)

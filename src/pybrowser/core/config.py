"""Application configuration and settings."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class BrowserConfig:
    """Immutable application-wide configuration settings."""

    app_name: str = "PyBrowser"
    version: str = "2.0.0"
    organization_name: str = "PyBrowser Org"
    organization_domain: str = "pybrowser.org"

    # Default URLs
    home_url: str = "https://duckduckgo.com"
    search_engine_template: str = "https://duckduckgo.com/?q={query}"

    # Window settings
    default_width: int = 1280
    default_height: int = 800
    theme: str = "dark"  # 'dark' or 'light'

    # Security settings
    enforce_https: bool = True
    javascript_enabled: bool = True
    plugins_enabled: bool = False
    auto_load_images: bool = True

    # Storage paths
    data_dir: Path = field(
        default_factory=lambda: Path(os.getenv("PYBROWSER_DATA_DIR") or Path.home() / ".pybrowser")
    )

    @property
    def database_path(self) -> Path:
        """Absolute path to the SQLite persistence database."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / "pybrowser.db"

    @property
    def downloads_dir(self) -> Path:
        """Default downloads directory."""
        downloads = Path.home() / "Downloads"
        return downloads if downloads.exists() else self.data_dir / "downloads"

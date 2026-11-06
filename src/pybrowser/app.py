"""Application bootstrap and lifecycle management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from pybrowser.core.config import BrowserConfig
from pybrowser.core.logger import get_logger, setup_root_logger
from pybrowser.services.storage_service import StorageService
from pybrowser.ui.main_window import MainWindow

logger = get_logger(__name__)


def find_assets_dir() -> Path:
    """Locate the assets directory relative to project root or source tree."""
    # Look in working directory first
    cwd_assets = Path.cwd() / "assets"
    if cwd_assets.exists() and (cwd_assets / "icons").exists():
        return cwd_assets

    # Look relative to this file's parent package
    pkg_assets = Path(__file__).resolve().parent.parent.parent / "assets"
    if pkg_assets.exists() and (pkg_assets / "icons").exists():
        return pkg_assets

    # Fallback to local assets
    return Path("assets").resolve()


def create_application() -> tuple[QApplication, MainWindow]:
    """Bootstrap and instantiate the PySide6 application and main window."""
    setup_root_logger()

    parser = argparse.ArgumentParser(description="PyBrowser Modern Desktop Browser")
    parser.add_argument("url", nargs="?", default=None, help="Initial URL or search term")
    args, _ = parser.parse_known_args()

    app = QApplication(sys.argv)
    app.setApplicationName("PyBrowser")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("PyBrowser Org")
    app.setOrganizationDomain("pybrowser.org")

    config = BrowserConfig()
    assets_dir = find_assets_dir()
    logger.info("Starting PyBrowser v%s with assets from %s", config.version, assets_dir)

    # Initialize persistence
    storage = StorageService(config.database_path)

    # Instantiate window
    window = MainWindow(config=config, assets_dir=assets_dir, storage_service=storage)

    if args.url:
        window.navigate_to(args.url)

    window.show()
    return app, window


def main() -> int:
    """Main CLI entry point returning process exit code."""
    app, _ = create_application()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

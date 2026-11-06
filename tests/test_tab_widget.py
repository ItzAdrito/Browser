"""Integration tests for BrowserTabWidget lifecycle in headless mode."""

from __future__ import annotations

import os
import sys

# Ensure offscreen rendering for headless CI environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication

from pybrowser.core.config import BrowserConfig
from pybrowser.ui.tab_widget import BrowserTabWidget


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_tab_lifecycle(qapp: QApplication, tmp_path) -> None:
    config = BrowserConfig(home_url="about:blank")
    icons_dir = tmp_path / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    tab_widget = BrowserTabWidget(config=config, icons_dir=icons_dir)
    assert tab_widget.count() == 0

    # Add initial tab
    view1 = tab_widget.add_new_tab(QUrl("about:blank"), "Tab 1")
    assert tab_widget.count() == 1
    assert tab_widget.current_view() == view1

    # Add second tab
    view2 = tab_widget.add_new_tab(QUrl("about:blank"), "Tab 2")
    assert tab_widget.count() == 2
    assert tab_widget.current_view() == view2

    # Close second tab
    tab_widget.close_tab(1)
    assert tab_widget.count() == 1
    assert tab_widget.current_view() == view1

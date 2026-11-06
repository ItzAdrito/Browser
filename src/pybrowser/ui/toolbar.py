"""Browser main toolbar containing navigation controls and omnibar."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QToolBar, QWidget

from pybrowser.ui.omnibar import Omnibar


class BrowserToolbar(QToolBar):
    """Main navigation and utility toolbar."""

    back_requested = Signal()
    forward_requested = Signal()
    reload_requested = Signal()
    stop_requested = Signal()
    home_requested = Signal()
    bookmarks_dialog_requested = Signal()
    history_dialog_requested = Signal()
    theme_toggle_requested = Signal()

    def __init__(self, icons_dir: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.icons_dir = icons_dir
        self.setMovable(False)
        self.setFloatable(False)

        self._reload_icon = QIcon(str(self.icons_dir / "reload.svg"))
        self._stop_icon = QIcon(str(self.icons_dir / "stop.svg"))
        self._is_loading = False

        self._init_ui()

    def _init_ui(self) -> None:
        # Navigation Actions
        self.back_action = QAction(QIcon(str(self.icons_dir / "back.svg")), "Back", self)
        self.back_action.setToolTip("Back (Alt+Left)")
        self.back_action.triggered.connect(self.back_requested)
        self.addAction(self.back_action)

        self.forward_action = QAction(QIcon(str(self.icons_dir / "forward.svg")), "Forward", self)
        self.forward_action.setToolTip("Forward (Alt+Right)")
        self.forward_action.triggered.connect(self.forward_requested)
        self.addAction(self.forward_action)

        self.reload_action = QAction(self._reload_icon, "Reload", self)
        self.reload_action.setToolTip("Reload page (Ctrl+R / F5)")
        self.reload_action.triggered.connect(self._on_reload_clicked)
        self.addAction(self.reload_action)

        self.home_action = QAction(QIcon(str(self.icons_dir / "home.svg")), "Home", self)
        self.home_action.setToolTip("Open Home page (Alt+Home)")
        self.home_action.triggered.connect(self.home_requested)
        self.addAction(self.home_action)

        # Embedded Omnibar
        self.omnibar = Omnibar(self.icons_dir, self)
        self.addWidget(self.omnibar)

        # Bookmarks Dialog Action
        self.bookmarks_action = QAction(QIcon(str(self.icons_dir / "star.svg")), "Bookmarks", self)
        self.bookmarks_action.setToolTip("View Bookmarks (Ctrl+B)")
        self.bookmarks_action.triggered.connect(self.bookmarks_dialog_requested)
        self.addAction(self.bookmarks_action)

        # History Dialog Action
        self.history_action = QAction(QIcon(str(self.icons_dir / "history.svg")), "History", self)
        self.history_action.setToolTip("View Browsing History (Ctrl+H)")
        self.history_action.triggered.connect(self.history_dialog_requested)
        self.addAction(self.history_action)

        # Theme Toggle Action
        self.theme_action = QAction(
            QIcon(str(self.icons_dir / "settings.svg")), "Toggle Theme", self
        )
        self.theme_action.setToolTip("Toggle Dark/Light Theme")
        self.theme_action.triggered.connect(self.theme_toggle_requested)
        self.addAction(self.theme_action)

    def _on_reload_clicked(self) -> None:
        if self._is_loading:
            self.stop_requested.emit()
        else:
            self.reload_requested.emit()

    def set_loading_state(self, is_loading: bool) -> None:
        """Toggle between reload and stop icon based on page loading activity."""
        self._is_loading = is_loading
        if is_loading:
            self.reload_action.setIcon(self._stop_icon)
            self.reload_action.setText("Stop")
            self.reload_action.setToolTip("Stop loading (Escape)")
        else:
            self.reload_action.setIcon(self._reload_icon)
            self.reload_action.setText("Reload")
            self.reload_action.setToolTip("Reload page (Ctrl+R / F5)")

    def update_nav_buttons(self, can_back: bool, can_forward: bool) -> None:
        """Update enabled states of back/forward buttons."""
        self.back_action.setEnabled(can_back)
        self.forward_action.setEnabled(can_forward)

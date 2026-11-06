"""Omnibar widget combining URL display, SSL indicator, and bookmark trigger."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QToolButton, QWidget

from pybrowser.core.logger import get_logger

logger = get_logger(__name__)


class Omnibar(QWidget):
    """Modern unified search and address bar with embedded status indicators."""

    navigate_requested = Signal(str)
    bookmark_toggled = Signal()

    def __init__(self, icons_dir: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._icons_dir = icons_dir

        self._lock_icon = QIcon(str(self._icons_dir / "lock.svg"))
        self._unlock_icon = QIcon(str(self._icons_dir / "unlock.svg"))
        self._star_icon = QIcon(str(self._icons_dir / "star.svg"))
        self._star_filled_icon = QIcon(str(self._icons_dir / "star-filled.svg"))

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Security Status Badge Button
        self.security_button = QToolButton(self)
        self.security_button.setIcon(self._lock_icon)
        self.security_button.setIconSize(QSize(16, 16))
        self.security_button.setToolTip("Secure Connection (HTTPS)")
        self.security_button.setStyleSheet("border: none; background: transparent;")

        # Address & Query Input Field
        self.input_field = QLineEdit(self)
        self.input_field.setObjectName("Omnibar")
        self.input_field.setPlaceholderText("Search with DuckDuckGo or enter web address")
        self.input_field.returnPressed.connect(self._on_return_pressed)

        # Bookmark Star Action inside Omnibar
        self.bookmark_button = QToolButton(self)
        self.bookmark_button.setIcon(self._star_icon)
        self.bookmark_button.setIconSize(QSize(16, 16))
        self.bookmark_button.setToolTip("Bookmark this tab")
        self.bookmark_button.setStyleSheet("border: none; background: transparent;")
        self.bookmark_button.clicked.connect(self.bookmark_toggled)

        layout.addWidget(self.security_button)
        layout.addWidget(self.input_field, stretch=1)
        layout.addWidget(self.bookmark_button)

    def _on_return_pressed(self) -> None:
        text = self.input_field.text().strip()
        if text:
            self.navigate_requested.emit(text)

    def update_state(self, url: str, is_secure: bool, is_bookmarked: bool) -> None:
        """Update address bar text, lock icon, and bookmark button status."""
        # Only update text if the user isn't actively editing
        if not self.input_field.hasFocus():
            self.input_field.setText(url)
            self.input_field.setCursorPosition(0)

        # Update security indicator
        if is_secure:
            self.security_button.setIcon(self._lock_icon)
            self.security_button.setToolTip("Connection is secure (HTTPS)")
        else:
            self.security_button.setIcon(self._unlock_icon)
            self.security_button.setToolTip("Connection is unencrypted (HTTP)")

        # Update bookmark star icon
        if is_bookmarked:
            self.bookmark_button.setIcon(self._star_filled_icon)
            self.bookmark_button.setToolTip("Edit bookmark for this page")
        else:
            self.bookmark_button.setIcon(self._star_icon)
            self.bookmark_button.setToolTip("Bookmark this tab")

    def text(self) -> str:
        """Return the current text entered in the omnibar."""
        return self.input_field.text()

    def set_text(self, text: str) -> None:
        """Set the text in the omnibar."""
        self.input_field.setText(text)

    def select_all(self) -> None:
        """Focus the input field and select all text for fast replacement."""
        self.input_field.setFocus()
        self.input_field.selectAll()

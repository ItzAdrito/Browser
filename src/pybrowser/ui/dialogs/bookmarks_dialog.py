"""Bookmarks management dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pybrowser.services.bookmark_service import BookmarkService


class BookmarksDialog(QDialog):
    """Interactive dialog for searching, opening, and managing bookmarks."""

    open_url_requested = Signal(str, bool)  # (url, in_new_tab)

    def __init__(self, bookmark_service: BookmarkService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.bookmark_service = bookmark_service
        self.setWindowTitle("Saved Bookmarks")
        self.resize(720, 480)

        self._init_ui()
        self._load_bookmarks()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Search filter
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Filter by title or URL...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Title", "URL", "Date Added"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self._on_open_current)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.open_current_btn = QPushButton("Open", self)
        self.open_current_btn.clicked.connect(self._on_open_current)

        self.open_new_tab_btn = QPushButton("Open in New Tab", self)
        self.open_new_tab_btn.clicked.connect(self._on_open_new_tab)

        self.delete_btn = QPushButton("Delete", self)
        self.delete_btn.setObjectName("SecondaryButton")
        self.delete_btn.clicked.connect(self._on_delete)

        self.close_btn = QPushButton("Close", self)
        self.close_btn.setObjectName("SecondaryButton")
        self.close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.open_current_btn)
        btn_layout.addWidget(self.open_new_tab_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

    def _load_bookmarks(self, search: str | None = None) -> None:
        bookmarks = self.bookmark_service.list_bookmarks(search)
        self.table.setRowCount(len(bookmarks))

        for row, bm in enumerate(bookmarks):
            title_item = QTableWidgetItem(bm.title)
            url_item = QTableWidgetItem(bm.url)
            date_str = bm.created_at.strftime("%Y-%m-%d %H:%M")
            date_item = QTableWidgetItem(date_str)

            # Store full URL in item data
            title_item.setData(Qt.ItemDataRole.UserRole, bm.url)

            self.table.setItem(row, 0, title_item)
            self.table.setItem(row, 1, url_item)
            self.table.setItem(row, 2, date_item)

    def _on_search_changed(self, text: str) -> None:
        self._load_bookmarks(text)

    def _get_selected_url(self) -> str | None:
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                return str(item.data(Qt.ItemDataRole.UserRole))
        return None

    def _on_open_current(self) -> None:
        url = self._get_selected_url()
        if url:
            self.open_url_requested.emit(url, False)
            self.accept()

    def _on_open_new_tab(self) -> None:
        url = self._get_selected_url()
        if url:
            self.open_url_requested.emit(url, True)
            self.accept()

    def _on_delete(self) -> None:
        url = self._get_selected_url()
        if url:
            self.bookmark_service.remove_bookmark(url)
            self._load_bookmarks(self.search_input.text())

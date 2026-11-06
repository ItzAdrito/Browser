"""Browsing history viewer dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pybrowser.services.history_service import HistoryService


class HistoryDialog(QDialog):
    """Interactive dialog for reviewing and clearing browsing history records."""

    open_url_requested = Signal(str, bool)  # (url, in_new_tab)

    def __init__(self, history_service: HistoryService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.history_service = history_service
        self.setWindowTitle("Browsing History")
        self.resize(800, 500)

        self._init_ui()
        self._load_history()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Search filter
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Filter history records...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Title", "URL", "Visits", "Last Visited"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
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

        self.delete_btn = QPushButton("Delete Entry", self)
        self.delete_btn.setObjectName("SecondaryButton")
        self.delete_btn.clicked.connect(self._on_delete_entry)

        self.clear_all_btn = QPushButton("Clear All History", self)
        self.clear_all_btn.setObjectName("SecondaryButton")
        self.clear_all_btn.setStyleSheet("color: #ef4444;")
        self.clear_all_btn.clicked.connect(self._on_clear_all)

        self.close_btn = QPushButton("Close", self)
        self.close_btn.setObjectName("SecondaryButton")
        self.close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.open_current_btn)
        btn_layout.addWidget(self.open_new_tab_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.clear_all_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

    def _load_history(self, search: str | None = None) -> None:
        entries = self.history_service.fetch_history(limit=250, search=search)
        self.table.setRowCount(len(entries))

        for row, item in enumerate(entries):
            title_cell = QTableWidgetItem(item.title)
            url_cell = QTableWidgetItem(item.url)
            count_cell = QTableWidgetItem(str(item.visit_count))
            date_str = item.visited_at.strftime("%Y-%m-%d %H:%M")
            date_cell = QTableWidgetItem(date_str)

            # Store ID and URL in custom role
            title_cell.setData(Qt.ItemDataRole.UserRole, item.url)
            title_cell.setData(Qt.ItemDataRole.UserRole + 1, item.id)

            self.table.setItem(row, 0, title_cell)
            self.table.setItem(row, 1, url_cell)
            self.table.setItem(row, 2, count_cell)
            self.table.setItem(row, 3, date_cell)

    def _on_search_changed(self, text: str) -> None:
        self._load_history(text)

    def _get_selected_row_data(self) -> tuple[str | None, int | None]:
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                url = item.data(Qt.ItemDataRole.UserRole)
                entry_id = item.data(Qt.ItemDataRole.UserRole + 1)
                return (str(url) if url else None, int(entry_id) if entry_id else None)
        return None, None

    def _on_open_current(self) -> None:
        url, _ = self._get_selected_row_data()
        if url:
            self.open_url_requested.emit(url, False)
            self.accept()

    def _on_open_new_tab(self) -> None:
        url, _ = self._get_selected_row_data()
        if url:
            self.open_url_requested.emit(url, True)
            self.accept()

    def _on_delete_entry(self) -> None:
        _, entry_id = self._get_selected_row_data()
        if entry_id is not None:
            self.history_service.delete_entry(entry_id)
            self._load_history(self.search_input.text())

    def _on_clear_all(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to permanently delete all browsing history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.history_service.clear_all()
            self._load_history()

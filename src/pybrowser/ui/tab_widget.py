"""Tab container widget managing multi-tab lifecycles and page switching."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, QUrl, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QTabWidget, QToolButton, QWidget

from pybrowser.core.config import BrowserConfig
from pybrowser.core.logger import get_logger
from pybrowser.ui.web_view import BrowserWebView

logger = get_logger(__name__)


class BrowserTabWidget(QTabWidget):
    """Multi-tab manager for isolated web browsing sessions."""

    current_url_changed = Signal(QUrl)
    current_title_changed = Signal(str)
    current_progress_changed = Signal(int)
    current_loading_finished = Signal(bool)
    page_loaded = Signal(str, str)  # (url, title)

    def __init__(
        self, config: BrowserConfig, icons_dir: Path, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.icons_dir = icons_dir

        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)

        # Tab close signal
        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self._on_current_tab_changed)

        # Add "+" button on the tab bar for new tabs
        self._add_tab_button = QToolButton(self)
        self._add_tab_button.setIcon(QIcon(str(self.icons_dir / "add.svg")))
        self._add_tab_button.setIconSize(QSize(14, 14))
        self._add_tab_button.setToolTip("Open new tab (Ctrl+T)")
        self._add_tab_button.setStyleSheet("border: none; background: transparent; padding: 4px;")
        self._add_tab_button.clicked.connect(lambda: self.add_new_tab())
        self.setCornerWidget(self._add_tab_button)

    def current_view(self) -> BrowserWebView | None:
        """Return the currently focused BrowserWebView instance."""
        widget = self.currentWidget()
        if isinstance(widget, BrowserWebView):
            return widget
        return None

    def add_new_tab(self, qurl: QUrl | None = None, label: str = "New Tab") -> BrowserWebView:
        """Instantiate and attach a new web view tab.

        Args:
            qurl: Target URL to navigate to, defaults to home_url.
            label: Initial title for the tab header.

        Returns:
            The created BrowserWebView instance.
        """
        if qurl is None:
            qurl = QUrl(self.config.home_url)

        view = BrowserWebView(self)
        index = self.addTab(view, label)

        # Connect page lifecycle signals
        view.urlChanged.connect(lambda u, v=view: self._on_view_url_changed(v, u))
        view.titleChanged.connect(lambda t, v=view: self._on_view_title_changed(v, t))
        view.loadProgress.connect(lambda p, v=view: self._on_view_load_progress(v, p))
        view.loadFinished.connect(lambda ok, v=view: self._on_view_load_finished(v, ok))
        view.iconChanged.connect(lambda ico, v=view: self._on_view_icon_changed(v, ico))

        # Handle links targeted for new tabs
        view.new_tab_requested.connect(self.add_new_tab)

        # Navigate to target URL
        view.load(qurl)

        self.setCurrentIndex(index)
        logger.debug("Created tab %d with url %s", index, qurl.toString())
        return view

    def close_tab(self, index: int) -> None:
        """Close and dispose of tab at specified index.

        Args:
            index: Tab index to terminate.
        """
        if self.count() <= 1:
            # If closing the last tab, reset it to home instead of leaving an empty window
            view = self.current_view()
            if view:
                view.load(QUrl(self.config.home_url))
            return

        widget = self.widget(index)
        self.removeTab(index)
        if widget is not None:
            widget.deleteLater()
            logger.debug("Safely closed and disposed tab at index %d", index)

    def _on_current_tab_changed(self, index: int) -> None:
        view = self.current_view()
        if view:
            self.current_url_changed.emit(view.url())
            self.current_title_changed.emit(view.title() or "PyBrowser")
            self.current_progress_changed.emit(100)

    def _on_view_url_changed(self, view: BrowserWebView, url: QUrl) -> None:
        if view == self.current_view():
            self.current_url_changed.emit(url)

    def _on_view_title_changed(self, view: BrowserWebView, title: str) -> None:
        index = self.indexOf(view)
        if index != -1:
            truncated = (title[:18] + "...") if len(title) > 20 else title
            self.setTabText(index, truncated or "Untitled")
            self.setTabToolTip(index, title)

        if view == self.current_view():
            self.current_title_changed.emit(title)

    def _on_view_load_progress(self, view: BrowserWebView, progress: int) -> None:
        if view == self.current_view():
            self.current_progress_changed.emit(progress)

    def _on_view_load_finished(self, view: BrowserWebView, ok: bool) -> None:
        if view == self.current_view():
            self.current_loading_finished.emit(ok)

        # Notify page loaded for history recording
        url_str = view.url().toString()
        title_str = view.title() or url_str
        if ok and url_str and not url_str.startswith("about:"):
            self.page_loaded.emit(url_str, title_str)

    def _on_view_icon_changed(self, view: BrowserWebView, icon: QIcon) -> None:
        index = self.indexOf(view)
        if index != -1 and not icon.isNull():
            self.setTabIcon(index, icon)

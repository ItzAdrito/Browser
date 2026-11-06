"""Main application window for PyBrowser."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtWidgets import QMainWindow, QProgressBar, QStatusBar

from pybrowser.core.config import BrowserConfig
from pybrowser.core.logger import get_logger
from pybrowser.core.url_sanitizer import URLSanitizer
from pybrowser.services.bookmark_service import BookmarkService
from pybrowser.services.download_service import DownloadService
from pybrowser.services.history_service import HistoryService
from pybrowser.services.storage_service import StorageService
from pybrowser.ui.dialogs.bookmarks_dialog import BookmarksDialog
from pybrowser.ui.dialogs.history_dialog import HistoryDialog
from pybrowser.ui.tab_widget import BrowserTabWidget
from pybrowser.ui.toolbar import BrowserToolbar

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window coordinating UI, tab management, and services."""

    def __init__(
        self,
        config: BrowserConfig,
        assets_dir: Path,
        storage_service: StorageService,
    ) -> None:
        super().__init__()
        self.config = config
        self.assets_dir = assets_dir
        self.icons_dir = assets_dir / "icons"
        self.styles_dir = assets_dir / "styles"

        self.current_theme = config.theme
        self.storage_service = storage_service
        self.bookmark_service = BookmarkService(self.storage_service)
        self.history_service = HistoryService(self.storage_service)
        self.url_sanitizer = URLSanitizer(self.config.search_engine_template)

        self._init_download_service()
        self._init_ui()
        self._setup_shortcuts()
        self._apply_theme(self.current_theme)

        # Open initial tab
        self.tab_widget.add_new_tab(QUrl(self.config.home_url))

    def _init_download_service(self) -> None:
        """Wire up download interception from QtWebEngine profile."""
        self.download_service = DownloadService(self.config.downloads_dir, self)
        profile = QWebEngineProfile.defaultProfile()
        profile.downloadRequested.connect(self.download_service.handle_download_requested)

        self.download_service.download_started.connect(
            lambda _id, fn: self.statusBar().showMessage(f"Download started: {fn}", 4000)
        )
        self.download_service.download_finished.connect(
            lambda _id, ok: self.statusBar().showMessage(
                "Download completed successfully!" if ok else "Download failed or was cancelled.",
                5000,
            )
        )

    def _init_ui(self) -> None:
        self.setWindowTitle(self.config.app_name)
        self.resize(self.config.default_width, self.config.default_height)
        self.setMinimumSize(800, 500)

        # Application Icon
        icon_path = self.icons_dir / "home.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Central Tab Manager
        self.tab_widget = BrowserTabWidget(self.config, self.icons_dir, self)
        self.setCentralWidget(self.tab_widget)

        # Main Toolbar
        self.toolbar = BrowserToolbar(self.icons_dir, self)
        self.addToolBar(self.toolbar)

        # Progress Bar inside Status Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximumWidth(140)
        self.progress_bar.setMaximumHeight(14)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)

        status_bar = QStatusBar(self)
        status_bar.addPermanentWidget(self.progress_bar)
        self.setStatusBar(status_bar)
        status_bar.showMessage("Ready", 3000)

        # Connect toolbar signals
        self.toolbar.back_requested.connect(self._navigate_back)
        self.toolbar.forward_requested.connect(self._navigate_forward)
        self.toolbar.reload_requested.connect(self._reload_current)
        self.toolbar.stop_requested.connect(self._stop_current)
        self.toolbar.home_requested.connect(self._navigate_home)
        self.toolbar.omnibar.navigate_requested.connect(self.navigate_to)
        self.toolbar.omnibar.bookmark_toggled.connect(self._toggle_current_bookmark)
        self.toolbar.bookmarks_dialog_requested.connect(self.show_bookmarks_dialog)
        self.toolbar.history_dialog_requested.connect(self.show_history_dialog)
        self.toolbar.theme_toggle_requested.connect(self.toggle_theme)

        # Connect tab signals
        self.tab_widget.current_url_changed.connect(self._on_url_changed)
        self.tab_widget.current_title_changed.connect(self._on_title_changed)
        self.tab_widget.current_progress_changed.connect(self._on_progress_changed)
        self.tab_widget.current_loading_finished.connect(self._on_loading_finished)
        self.tab_widget.page_loaded.connect(self.history_service.log_visit)

    def _setup_shortcuts(self) -> None:
        """Register keyboard shortcuts for productivity."""
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.tab_widget.add_new_tab())
        QShortcut(
            QKeySequence("Ctrl+W"),
            self,
            lambda: self.tab_widget.close_tab(self.tab_widget.currentIndex()),
        )
        QShortcut(QKeySequence("Ctrl+L"), self, self.toolbar.omnibar.select_all)
        QShortcut(QKeySequence("Ctrl+R"), self, self._reload_current)
        QShortcut(QKeySequence("F5"), self, self._reload_current)
        QShortcut(QKeySequence("Escape"), self, self._stop_current)
        QShortcut(QKeySequence("Alt+Left"), self, self._navigate_back)
        QShortcut(QKeySequence("Alt+Right"), self, self._navigate_forward)
        QShortcut(QKeySequence("Alt+Home"), self, self._navigate_home)
        QShortcut(QKeySequence("Ctrl+B"), self, self.show_bookmarks_dialog)
        QShortcut(QKeySequence("Ctrl+H"), self, self.show_history_dialog)

        # Zoom Shortcuts
        QShortcut(QKeySequence("Ctrl++"), self, self._zoom_in)
        QShortcut(QKeySequence("Ctrl+="), self, self._zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self._zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self._reset_zoom)

    # ---------------------------------------------------------
    # Navigation & Actions
    # ---------------------------------------------------------
    def navigate_to(self, target: str) -> None:
        """Sanitize target text and navigate current tab."""
        resolved_url = self.url_sanitizer.resolve(target)
        view = self.tab_widget.current_view()
        if view:
            view.load(QUrl(resolved_url))

    def _navigate_back(self) -> None:
        view = self.tab_widget.current_view()
        if view:
            view.back()

    def _navigate_forward(self) -> None:
        view = self.tab_widget.current_view()
        if view:
            view.forward()

    def _reload_current(self) -> None:
        view = self.tab_widget.current_view()
        if view:
            view.reload()

    def _stop_current(self) -> None:
        view = self.tab_widget.current_view()
        if view:
            view.stop()

    def _navigate_home(self) -> None:
        self.navigate_to(self.config.home_url)

    def _zoom_in(self) -> None:
        view = self.tab_widget.current_view()
        if view:
            view.zoom_in()

    def _zoom_out(self) -> None:
        view = self.tab_widget.current_view()
        if view:
            view.zoom_out()

    def _reset_zoom(self) -> None:
        view = self.tab_widget.current_view()
        if view:
            view.reset_zoom()

    def _toggle_current_bookmark(self) -> None:
        view = self.tab_widget.current_view()
        if not view:
            return
        url_str = view.url().toString()
        title_str = view.title() or url_str
        if not url_str or url_str.startswith("about:"):
            return

        is_now_bookmarked = self.bookmark_service.toggle_bookmark(url_str, title_str)
        is_secure = self.url_sanitizer.is_secure(url_str)
        self.toolbar.omnibar.update_state(url_str, is_secure, is_now_bookmarked)
        self.statusBar().showMessage(
            "Bookmark saved" if is_now_bookmarked else "Bookmark removed", 2500
        )

    # ---------------------------------------------------------
    # Tab / State Callbacks
    # ---------------------------------------------------------
    def _on_url_changed(self, url: QUrl) -> None:
        url_str = url.toString()
        is_secure = self.url_sanitizer.is_secure(url_str)
        is_bookmarked = self.bookmark_service.is_bookmarked(url_str)
        self.toolbar.omnibar.update_state(url_str, is_secure, is_bookmarked)

        view = self.tab_widget.current_view()
        if view:
            self.toolbar.update_nav_buttons(
                view.history().canGoBack(), view.history().canGoForward()
            )

    def _on_title_changed(self, title: str) -> None:
        if title:
            self.setWindowTitle(f"{title} — {self.config.app_name}")
        else:
            self.setWindowTitle(self.config.app_name)

    def _on_progress_changed(self, progress: int) -> None:
        if progress < 100:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(progress)
            self.toolbar.set_loading_state(True)
        else:
            self.progress_bar.setVisible(False)
            self.toolbar.set_loading_state(False)

    def _on_loading_finished(self, ok: bool) -> None:
        self.progress_bar.setVisible(False)
        self.toolbar.set_loading_state(False)
        view = self.tab_widget.current_view()
        if view:
            self.toolbar.update_nav_buttons(
                view.history().canGoBack(), view.history().canGoForward()
            )
        status_msg = "Page loaded successfully" if ok else "Navigation cancelled or failed"
        self.statusBar().showMessage(status_msg, 2500)

    # ---------------------------------------------------------
    # Dialogs & Themes
    # ---------------------------------------------------------
    def show_bookmarks_dialog(self) -> None:
        """Display the bookmarks management modal."""
        dialog = BookmarksDialog(self.bookmark_service, self)
        dialog.open_url_requested.connect(self._handle_dialog_open_url)
        dialog.exec()

    def show_history_dialog(self) -> None:
        """Display the history viewer modal."""
        dialog = HistoryDialog(self.history_service, self)
        dialog.open_url_requested.connect(self._handle_dialog_open_url)
        dialog.exec()

    def _handle_dialog_open_url(self, url: str, in_new_tab: bool) -> None:
        if in_new_tab:
            self.tab_widget.add_new_tab(QUrl(url))
        else:
            self.navigate_to(url)

    def toggle_theme(self) -> None:
        """Toggle between dark and light QSS stylesheet."""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self._apply_theme(self.current_theme)

    def _apply_theme(self, theme_name: str) -> None:
        style_file = self.styles_dir / f"{theme_name}.qss"
        if style_file.exists():
            stylesheet = style_file.read_text(encoding="utf-8")
            self.setStyleSheet(stylesheet)
            logger.info("Applied theme: %s", theme_name)

"""Custom WebEngineView component with security hardening and enhanced navigation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QAction, QContextMenuEvent
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMenu

from pybrowser.core.logger import get_logger

if TYPE_CHECKING:
    from pybrowser.ui.tab_widget import BrowserTabWidget

logger = get_logger(__name__)


class CustomWebPage(QWebEnginePage):
    """Customized WebEnginePage supporting link delegation to new tabs."""

    new_tab_requested = Signal(QUrl)

    def createWindow(self, _type: QWebEnginePage.WebWindowType) -> QWebEnginePage:  # noqa: N802
        """Handle target='_blank' and window.open requests by emitting a new tab request."""
        logger.debug("Window creation requested: %s", _type)
        # Create an ephemeral page that intercepts the first URL load and forwards to a new tab
        new_page = CustomWebPage(self.profile(), self.parent())
        new_page.urlChanged.connect(self._handle_external_url_request)
        return new_page

    def _handle_external_url_request(self, url: QUrl) -> None:
        if url.isValid() and not url.isEmpty():
            self.new_tab_requested.emit(url)


class BrowserWebView(QWebEngineView):
    """Encapsulated web view widget with custom context menu and event hooks."""

    new_tab_requested = Signal(QUrl)

    def __init__(self, parent: BrowserTabWidget | None = None) -> None:
        super().__init__(parent)
        self._configure_security_settings()

        # Set custom web page
        page = CustomWebPage(self)
        page.new_tab_requested.connect(self.new_tab_requested)
        self.setPage(page)

    def _configure_security_settings(self) -> None:
        """Apply security hardening to web engine profile settings."""
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        # Disable insecure plugin execution
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # noqa: N802
        """Render a clean, contextual right-click menu."""
        menu = QMenu(self)

        back_action = QAction("Back", self)
        back_action.setEnabled(self.history().canGoBack())
        back_action.triggered.connect(self.back)
        menu.addAction(back_action)

        forward_action = QAction("Forward", self)
        forward_action.setEnabled(self.history().canGoForward())
        forward_action.triggered.connect(self.forward)
        menu.addAction(forward_action)

        reload_action = QAction("Reload", self)
        reload_action.triggered.connect(self.reload)
        menu.addAction(reload_action)

        menu.addSeparator()

        copy_url_action = QAction("Copy Page Address", self)
        copy_url_action.triggered.connect(self._copy_current_url)
        menu.addAction(copy_url_action)

        menu.exec(event.globalPos())

    def _copy_current_url(self) -> None:
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.url().toString())

    def zoom_in(self) -> None:
        """Increase page zoom factor."""
        factor = min(self.zoomFactor() + 0.1, 3.0)
        self.setZoomFactor(factor)

    def zoom_out(self) -> None:
        """Decrease page zoom factor."""
        factor = max(self.zoomFactor() - 0.1, 0.25)
        self.setZoomFactor(factor)

    def reset_zoom(self) -> None:
        """Reset page zoom to 100%."""
        self.setZoomFactor(1.0)

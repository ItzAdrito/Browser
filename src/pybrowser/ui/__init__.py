"""UI package for PyBrowser."""

from pybrowser.ui.main_window import MainWindow
from pybrowser.ui.omnibar import Omnibar
from pybrowser.ui.tab_widget import BrowserTabWidget
from pybrowser.ui.toolbar import BrowserToolbar
from pybrowser.ui.web_view import BrowserWebView

__all__ = [
    "BrowserTabWidget",
    "BrowserToolbar",
    "BrowserWebView",
    "MainWindow",
    "Omnibar",
]

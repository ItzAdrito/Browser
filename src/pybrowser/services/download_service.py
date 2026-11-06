"""Download management service for PyBrowser."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest

from pybrowser.core.logger import get_logger

logger = get_logger(__name__)


class DownloadItemState:
    """State wrapper for an active or completed download."""

    def __init__(self, request: QWebEngineDownloadRequest) -> None:
        self.request = request
        self.id = request.id()
        self.filename = Path(request.downloadFileName()).name
        self.total_bytes = request.totalBytes()
        self.received_bytes = request.receivedBytes()
        self.state = request.state()


class DownloadService(QObject):
    """Tracks and orchestrates file downloads initiated in web pages."""

    download_started = Signal(str, str)  # (id, filename)
    download_progress = Signal(str, int, int)  # (id, received, total)
    download_finished = Signal(str, bool)  # (id, success)

    def __init__(self, default_download_dir: Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.download_dir = default_download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self._active_downloads: dict[str, QWebEngineDownloadRequest] = {}

    def handle_download_requested(self, download: QWebEngineDownloadRequest) -> None:
        """Handle download request from QWebEngineProfile."""
        filename = download.downloadFileName() or "download"
        target_path = self.download_dir / filename

        # Avoid collision
        counter = 1
        stem = target_path.stem
        suffix = target_path.suffix
        while target_path.exists():
            target_path = self.download_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        download.setDownloadDirectory(str(self.download_dir))
        download.setDownloadFileName(target_path.name)

        req_id = str(download.id())
        self._active_downloads[req_id] = download

        download.receivedBytesChanged.connect(
            lambda: self.download_progress.emit(
                req_id, download.receivedBytes(), download.totalBytes()
            )
        )
        download.stateChanged.connect(lambda state: self._on_state_changed(req_id, download, state))

        logger.info("Starting download: %s to %s", filename, target_path)
        download.accept()
        self.download_started.emit(req_id, target_path.name)

    def _on_state_changed(
        self,
        req_id: str,
        download: QWebEngineDownloadRequest,
        state: QWebEngineDownloadRequest.DownloadState,
    ) -> None:
        if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            logger.info("Download completed: %s", download.downloadFileName())
            self.download_finished.emit(req_id, True)
            self._active_downloads.pop(req_id, None)
        elif (
            state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled
            or state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted
        ):
            logger.warning("Download failed/cancelled: %s", download.downloadFileName())
            self.download_finished.emit(req_id, False)
            self._active_downloads.pop(req_id, None)

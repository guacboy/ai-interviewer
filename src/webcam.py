"""Webcam capture for the live preview and facial emotion analysis."""

import threading
import time

import numpy as np

FRAME_INTERVAL = 1 / 30


class WebcamCapture:
    """Captures frames from a webcam in a background thread."""

    def __init__(self, capture_factory=None):
        self._capture_factory = capture_factory or self._default_capture_factory
        self._capture = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._lock = threading.Lock()
        self._frame: np.ndarray | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Open the camera and start capturing frames in the background."""
        if self._running:
            return

        self._capture = self._capture_factory()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop capturing and release the camera."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

        if self._capture is not None:
            self._capture.release()
            self._capture = None

        with self._lock:
            self._frame = None

    def get_frame(self) -> np.ndarray | None:
        """Return the most recently captured frame (BGR), or None if unavailable."""
        with self._lock:
            return None if self._frame is None else self._frame.copy()

    def _loop(self) -> None:
        while self._running:
            ok, frame = self._capture.read()
            if ok:
                with self._lock:
                    self._frame = frame
            time.sleep(FRAME_INTERVAL)

    @staticmethod
    def _default_capture_factory():
        import cv2

        return cv2.VideoCapture(0)

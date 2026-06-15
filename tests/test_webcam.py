import time

import numpy as np

from webcam import WebcamCapture


class FakeCapture:
    def __init__(self, frame=None):
        self.frame = frame
        self.released = False

    def read(self):
        if self.frame is None:
            return False, None
        return True, self.frame.copy()

    def release(self):
        self.released = True


class TestWebcamCapture:
    def test_not_running_initially(self):
        capture = WebcamCapture(capture_factory=lambda: FakeCapture())

        assert not capture.is_running

    def test_get_frame_returns_none_before_start(self):
        capture = WebcamCapture(capture_factory=lambda: FakeCapture())

        assert capture.get_frame() is None

    def test_start_marks_running(self):
        capture = WebcamCapture(capture_factory=lambda: FakeCapture())

        capture.start()

        assert capture.is_running
        capture.stop()

    def test_starting_twice_is_a_no_op(self):
        captures = []

        def factory():
            cap = FakeCapture()
            captures.append(cap)
            return cap

        capture = WebcamCapture(capture_factory=factory)
        capture.start()
        capture.start()

        assert len(captures) == 1
        capture.stop()

    def test_stop_releases_capture_and_clears_frame(self):
        fake = FakeCapture(frame=np.zeros((2, 2, 3), dtype=np.uint8))
        capture = WebcamCapture(capture_factory=lambda: fake)

        capture.start()
        capture.stop()

        assert fake.released
        assert not capture.is_running
        assert capture.get_frame() is None

    def test_captures_frames_in_background(self):
        frame = np.ones((2, 2, 3), dtype=np.uint8)
        capture = WebcamCapture(capture_factory=lambda: FakeCapture(frame=frame))

        capture.start()
        for _ in range(50):
            if capture.get_frame() is not None:
                break
            time.sleep(0.01)

        result = capture.get_frame()
        capture.stop()

        assert result is not None
        np.testing.assert_array_equal(result, frame)

    def test_no_frame_when_camera_unavailable(self):
        capture = WebcamCapture(capture_factory=lambda: FakeCapture(frame=None))

        capture.start()
        time.sleep(0.02)
        result = capture.get_frame()
        capture.stop()

        assert result is None

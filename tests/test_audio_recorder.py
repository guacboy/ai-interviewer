import numpy as np

from audio_recorder import AudioRecorder


class FakeStream:
    def __init__(self):
        self.started = False
        self.closed = False

    def start(self):
        self.started = True

    def stop(self):
        self.started = False

    def close(self):
        self.closed = True


class TestAudioRecorder:
    def test_not_recording_initially(self):
        recorder = AudioRecorder(stream_factory=lambda sr, cb: FakeStream())
        assert not recorder.is_recording

    def test_start_marks_recording_and_starts_stream(self):
        stream = FakeStream()
        recorder = AudioRecorder(stream_factory=lambda sr, cb: stream)

        recorder.start()

        assert recorder.is_recording
        assert stream.started

    def test_starting_twice_is_a_no_op(self):
        streams = []

        def factory(sr, cb):
            stream = FakeStream()
            streams.append(stream)
            return stream

        recorder = AudioRecorder(stream_factory=factory)

        recorder.start()
        recorder.start()

        assert len(streams) == 1

    def test_stop_without_audio_returns_empty_array(self):
        recorder = AudioRecorder(stream_factory=lambda sr, cb: FakeStream())
        recorder.start()

        audio = recorder.stop()

        assert audio.size == 0
        assert not recorder.is_recording

    def test_stop_closes_the_stream(self):
        stream = FakeStream()
        recorder = AudioRecorder(stream_factory=lambda sr, cb: stream)

        recorder.start()
        recorder.stop()

        assert stream.closed
        assert not stream.started

    def test_stop_concatenates_recorded_frames(self):
        recorder = AudioRecorder(stream_factory=lambda sr, cb: FakeStream())
        recorder.start()

        recorder._callback(np.array([[0.1], [0.2]], dtype=np.float32), 2, None, None)
        recorder._callback(np.array([[0.3]], dtype=np.float32), 1, None, None)

        audio = recorder.stop()

        np.testing.assert_allclose(audio, [0.1, 0.2, 0.3])

    def test_starting_again_clears_previous_frames(self):
        recorder = AudioRecorder(stream_factory=lambda sr, cb: FakeStream())

        recorder.start()
        recorder._callback(np.array([[0.5]], dtype=np.float32), 1, None, None)
        recorder.stop()

        recorder.start()
        audio = recorder.stop()

        assert audio.size == 0

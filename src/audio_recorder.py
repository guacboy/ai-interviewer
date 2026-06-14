"""Microphone audio recording for interview answers."""

import numpy as np

SAMPLE_RATE = 16000


class AudioRecorder:
    """Records mono audio from an input stream until stopped."""

    def __init__(self, samplerate: int = SAMPLE_RATE, stream_factory=None):
        self.samplerate = samplerate
        self._stream_factory = stream_factory or self._default_stream_factory
        self._frames: list[np.ndarray] = []
        self._stream = None

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    def start(self) -> None:
        """Start recording from the microphone."""
        if self.is_recording:
            return

        self._frames = []
        self._stream = self._stream_factory(self.samplerate, self._callback)
        self._stream.start()

    def stop(self) -> np.ndarray:
        """Stop recording and return the recorded audio as mono float32 samples."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._frames:
            return np.zeros(0, dtype=np.float32)

        return np.concatenate(self._frames, axis=0).reshape(-1)

    def _callback(self, indata, frames, time, status) -> None:
        self._frames.append(indata.copy())

    @staticmethod
    def _default_stream_factory(samplerate, callback):
        import sounddevice as sd

        return sd.InputStream(samplerate=samplerate, channels=1, dtype="float32", callback=callback)

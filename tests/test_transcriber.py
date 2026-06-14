from unittest.mock import patch

import numpy as np

import transcriber


class TestTranscribeAudio:
    def test_empty_audio_returns_empty_string(self):
        assert transcriber.transcribe_audio(np.zeros(0, dtype=np.float32)) == ""

    def test_strips_whitespace_from_pipeline_result(self):
        fake_pipeline = lambda inputs: {"text": "  hello world  "}

        with patch.object(transcriber, "_load_pipeline", return_value=fake_pipeline):
            result = transcriber.transcribe_audio(np.ones(16000, dtype=np.float32))

        assert result == "hello world"

    def test_passes_audio_and_samplerate_to_pipeline(self):
        captured = {}

        def fake_pipeline(inputs):
            captured.update(inputs)
            return {"text": "ok"}

        with patch.object(transcriber, "_load_pipeline", return_value=fake_pipeline):
            audio = np.ones(8000, dtype=np.float32)
            transcriber.transcribe_audio(audio, samplerate=8000)

        assert captured["sampling_rate"] == 8000
        np.testing.assert_array_equal(captured["raw"], audio)

"""Speech-to-text transcription of recorded answers using a local Whisper model."""

import numpy as np

DEFAULT_MODEL = "openai/whisper-base"

_pipeline = None
_model_name = None


def _load_pipeline(model_name: str = DEFAULT_MODEL):
    """Load (and cache) the automatic-speech-recognition pipeline for `model_name`."""
    global _pipeline, _model_name

    if _pipeline is None or _model_name != model_name:
        from transformers import pipeline as hf_pipeline

        _pipeline = hf_pipeline("automatic-speech-recognition", model=model_name)
        _model_name = model_name

    return _pipeline


def transcribe_audio(audio: np.ndarray, samplerate: int = 16000, model_name: str = DEFAULT_MODEL) -> str:
    """Transcribe mono float32 audio samples to text."""
    if audio.size == 0:
        return ""

    asr = _load_pipeline(model_name)
    result = asr({"raw": audio, "sampling_rate": samplerate})
    return result["text"].strip()

"""Text-to-speech for reading interview questions aloud."""

DEFAULT_RATE = 175

# Set to a voice id from `list_voices()` to override the system default voice.
DEFAULT_VOICE = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"

#TODO(fix): tts doesn't work if you navigate mid sentence - will remove the navigation in the future anyways.

def list_voices() -> list[dict]:
    """Return the available system TTS voices as a list of {id, name} dicts."""
    import pyttsx3

    engine = pyttsx3.init()
    return [{"id": voice.id, "name": voice.name} for voice in engine.getProperty("voices")]


class Speaker:
    """Speaks text aloud using the system's text-to-speech engine."""

    def __init__(self, rate: int = DEFAULT_RATE, voice: str | None = DEFAULT_VOICE, engine_factory=None):
        self.rate = rate
        self.voice = voice
        self._engine_factory = engine_factory or self._default_engine_factory
        self._engine = None

    def speak(self, text: str) -> None:
        """Speak `text` aloud, blocking until finished."""
        if not text:
            return

        engine = self._get_engine()
        engine.say(text)
        engine.runAndWait()

    def stop(self) -> None:
        """Stop any speech currently in progress."""
        if self._engine is not None:
            self._engine.stop()

    def _get_engine(self):
        if self._engine is None:
            self._engine = self._engine_factory()
            self._engine.setProperty("rate", self.rate)
            if self.voice:
                self._engine.setProperty("voice", self.voice)

        return self._engine

    @staticmethod
    def _default_engine_factory():
        import pyttsx3

        return pyttsx3.init()

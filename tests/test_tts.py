from tts import Speaker


class FakeEngine:
    def __init__(self):
        self.said: list[str] = []
        self.properties: dict = {}
        self.ran = False
        self.stopped = False

    def say(self, text):
        self.said.append(text)

    def runAndWait(self):
        self.ran = True

    def setProperty(self, name, value):
        self.properties[name] = value

    def stop(self):
        self.stopped = True


class TestSpeaker:
    def test_speak_says_text_and_runs(self):
        engine = FakeEngine()
        speaker = Speaker(engine_factory=lambda: engine)

        speaker.speak("hello")

        assert engine.said == ["hello"]
        assert engine.ran

    def test_speak_empty_text_is_a_no_op(self):
        engine = FakeEngine()
        speaker = Speaker(engine_factory=lambda: engine)

        speaker.speak("")

        assert engine.said == []
        assert not engine.ran

    def test_engine_is_created_lazily_and_cached(self):
        created = []

        def factory():
            created.append(FakeEngine())
            return created[-1]

        speaker = Speaker(engine_factory=factory)
        speaker.speak("one")
        speaker.speak("two")

        assert len(created) == 1
        assert created[0].said == ["one", "two"]

    def test_rate_is_applied_to_engine(self):
        engine = FakeEngine()
        speaker = Speaker(rate=200, engine_factory=lambda: engine)

        speaker.speak("hello")

        assert engine.properties["rate"] == 200

    def test_stop_stops_the_engine(self):
        engine = FakeEngine()
        speaker = Speaker(engine_factory=lambda: engine)
        speaker.speak("hello")

        speaker.stop()

        assert engine.stopped

    def test_stop_before_speaking_is_a_no_op(self):
        speaker = Speaker(engine_factory=lambda: FakeEngine())

        speaker.stop()

    def test_voice_is_applied_to_engine(self):
        engine = FakeEngine()
        speaker = Speaker(voice="voice-id", engine_factory=lambda: engine)

        speaker.speak("hello")

        assert engine.properties["voice"] == "voice-id"

    def test_no_voice_set_when_voice_is_none(self):
        engine = FakeEngine()
        speaker = Speaker(voice=None, engine_factory=lambda: engine)

        speaker.speak("hello")

        assert "voice" not in engine.properties

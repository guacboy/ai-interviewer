import numpy as np

from emotion_detector import EmotionDetector


class FakeCascade:
    def __init__(self, faces):
        self.faces = faces

    def detectMultiScale(self, gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)):
        return self.faces


class TestEmotionDetector:
    def test_detect_returns_none_when_no_face_found(self):
        detector = EmotionDetector(
            face_cascade_factory=lambda: FakeCascade([]),
            pipeline_factory=lambda model: (lambda image: [{"label": "happy", "score": 0.9}]),
        )

        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        assert detector.detect(frame) is None

    def test_detect_returns_top_emotion_for_detected_face(self):
        results = [
            {"label": "neutral", "score": 0.2},
            {"label": "happy", "score": 0.7},
            {"label": "sad", "score": 0.1},
        ]
        detector = EmotionDetector(
            face_cascade_factory=lambda: FakeCascade([(0, 0, 50, 50)]),
            pipeline_factory=lambda model: (lambda image: results),
        )

        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        result = detector.detect(frame)

        assert result == {"label": "happy", "score": 0.7}

    def test_pipeline_is_created_lazily_and_cached(self):
        created = []

        def pipeline_factory(model):
            created.append(model)
            return lambda image: [{"label": "neutral", "score": 1.0}]

        detector = EmotionDetector(
            face_cascade_factory=lambda: FakeCascade([(0, 0, 50, 50)]),
            pipeline_factory=pipeline_factory,
        )

        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        detector.detect(frame)
        detector.detect(frame)

        assert len(created) == 1

    def test_face_cascade_is_created_lazily_and_cached(self):
        created = []

        def cascade_factory():
            created.append(object())
            return FakeCascade([(0, 0, 50, 50)])

        detector = EmotionDetector(
            face_cascade_factory=cascade_factory,
            pipeline_factory=lambda model: (lambda image: [{"label": "neutral", "score": 1.0}]),
        )

        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        detector.detect(frame)
        detector.detect(frame)

        assert len(created) == 1

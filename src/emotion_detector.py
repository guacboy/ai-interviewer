"""Facial emotion detection from webcam frames."""

import numpy as np

DEFAULT_MODEL = "trpakov/vit-face-expression"


class EmotionDetector:
    """Detects the dominant facial emotion in a video frame."""

    def __init__(self, model_name: str = DEFAULT_MODEL, pipeline_factory=None, face_cascade_factory=None):
        self.model_name = model_name
        self._pipeline_factory = pipeline_factory or self._default_pipeline_factory
        self._face_cascade_factory = face_cascade_factory or self._default_face_cascade_factory
        self._pipeline = None
        self._face_cascade = None

    def detect(self, frame: np.ndarray) -> dict | None:
        """Return {"label": str, "score": float} for the dominant emotion, or None if no face is found."""
        face = self._extract_face(frame)
        if face is None:
            return None

        results = self._get_pipeline()(face)
        if not results:
            return None

        top = max(results, key=lambda r: r["score"])
        return {"label": top["label"], "score": top["score"]}

    def _extract_face(self, frame: np.ndarray):
        import cv2
        from PIL import Image

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._get_face_cascade().detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        if len(faces) == 0:
            return None

        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        face_rgb = cv2.cvtColor(frame[y : y + h, x : x + w], cv2.COLOR_BGR2RGB)
        return Image.fromarray(face_rgb)

    def _get_pipeline(self):
        if self._pipeline is None:
            self._pipeline = self._pipeline_factory(self.model_name)

        return self._pipeline

    def _get_face_cascade(self):
        if self._face_cascade is None:
            self._face_cascade = self._face_cascade_factory()

        return self._face_cascade

    @staticmethod
    def _default_pipeline_factory(model_name):
        from transformers import pipeline

        return pipeline("image-classification", model=model_name)

    @staticmethod
    def _default_face_cascade_factory():
        import cv2

        return cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

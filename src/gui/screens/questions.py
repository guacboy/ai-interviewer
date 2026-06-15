"""Questions screen: displays generated interview questions with navigation."""

import threading

import numpy as np
import pygame

from audio_recorder import AudioRecorder
from emotion_detector import EmotionDetector
from transcriber import transcribe_audio
from tts import Speaker
from webcam import WebcamCapture

from .. import constants as c
from ..widgets import Button, TextBox, wrap_text
from .base import Screen

#TODO(feat): add an "interviewer" with the questions appearing on top as an overlay

EMOTION_DETECT_INTERVAL = 2.0


class QuestionsScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.question_font = pygame.font.SysFont(None, 32)
        self.counter_font = pygame.font.SysFont(None, 22)
        button_font = pygame.font.SysFont(None, 32)

        self.questions: list[str] = []
        self.answers: list[str] = []
        self.index = 0

        self.recorder = AudioRecorder()
        self.is_recording = False
        self._transcribe_worker: threading.Thread | None = None
        self._transcribe_result: tuple[int, str] | None = None
        self._transcribe_error: str | None = None

        self.speaker = Speaker()
        self.is_speaking = False
        self._speak_worker: threading.Thread | None = None

        self.webcam = WebcamCapture()
        self.emotion_detector = EmotionDetector()
        self.current_emotion: dict | None = None
        self._emotion_worker: threading.Thread | None = None
        self._emotion_result: dict | None = None
        self._emotion_timer = 0.0
        self.webcam_rect = pygame.Rect(c.SCREEN_WIDTH - 200, 20, 180, 135)

        self.prev_button = Button((60, c.SCREEN_HEIGHT - 90, 140, 50), "Previous", button_font, on_click=self._prev)
        self.next_button = Button(
            (c.SCREEN_WIDTH - 200, c.SCREEN_HEIGHT - 90, 140, 50), "Next", button_font, on_click=self._next
        )
        self.restart_button = Button(
            ((c.SCREEN_WIDTH - 160) // 2, c.SCREEN_HEIGHT - 90, 160, 50),
            "New Resume",
            button_font,
            on_click=self._restart,
        )
        self.record_button = Button(
            ((c.SCREEN_WIDTH - 220) // 2, c.SCREEN_HEIGHT - 160, 220, 50),
            "Record Answer",
            button_font,
            on_click=self._toggle_recording,
        )
        self.answer_box = TextBox(
            (60, 280, c.SCREEN_WIDTH - 120, 150),
            pygame.font.SysFont(None, 24),
            placeholder="Type your answer here, or record audio above.",
        )

    def on_enter(self, **kwargs) -> None:
        if self.recorder.is_recording:
            self.recorder.stop()
        self._stop_speaking()

        self.questions = kwargs.get("questions", [])
        self.answers = [""] * len(self.questions)
        self.index = 0
        self.is_recording = False
        self.record_button.text = "Record Answer"
        self.record_button.enabled = True
        self._transcribe_worker = None
        self._transcribe_result = None
        self._transcribe_error = None
        self.answer_box.set_text(self.answers[0] if self.questions else "")
        self.current_emotion = None
        self._emotion_result = None
        self._emotion_timer = 0.0
        self.webcam.start()
        self._update_buttons()
        self._speak_current_question()

    def _restart(self) -> None:
        self._stop_speaking()
        self.webcam.stop()
        self.app.switch_to("resume_input")

    def _save_current_answer(self) -> None:
        if 0 <= self.index < len(self.answers):
            self.answers[self.index] = self.answer_box.text

    def _prev(self) -> None:
        if self.index > 0 and not self._is_busy():
            self._stop_speaking()
            self._save_current_answer()
            self.index -= 1
            self.answer_box.set_text(self.answers[self.index])
            self._update_buttons()
            self._speak_current_question()

    def _next(self) -> None:
        if self.index < len(self.questions) - 1 and not self._is_busy():
            self._stop_speaking()
            self._save_current_answer()
            self.index += 1
            self.answer_box.set_text(self.answers[self.index])
            self._update_buttons()
            self._speak_current_question()

    def _is_busy(self) -> bool:
        return self.is_recording or bool(self._transcribe_worker and self._transcribe_worker.is_alive())

    def _update_buttons(self) -> None:
        busy = self._is_busy()
        self.prev_button.enabled = self.index > 0 and not busy
        self.next_button.enabled = self.index < len(self.questions) - 1 and not busy
        self.restart_button.enabled = not busy
        self.record_button.enabled = not self.is_speaking and not (
            self._transcribe_worker and self._transcribe_worker.is_alive()
        )

    def _toggle_recording(self) -> None:
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        self.recorder.start()
        self.is_recording = True
        self.record_button.text = "Stop Recording"
        self._transcribe_error = None
        self._update_buttons()

    def _stop_recording(self) -> None:
        audio = self.recorder.stop()
        self.is_recording = False
        self.record_button.text = "Record Answer"
        self.record_button.enabled = False

        index = self.index
        self._transcribe_worker = threading.Thread(target=self._transcribe, args=(index, audio), daemon=True)
        self._transcribe_worker.start()
        self._update_buttons()

    def _transcribe(self, index: int, audio) -> None:
        try:
            text = transcribe_audio(audio)
        except Exception as exc:
            self._transcribe_error = f"Transcription failed: {exc}"
            return

        self._transcribe_result = (index, text)

    def _speak_current_question(self) -> None:
        if not self.questions:
            return

        self._stop_speaking()
        self.is_speaking = True
        self._speak_worker = threading.Thread(
            target=self.speaker.speak, args=(self.questions[self.index],), daemon=True
        )
        self._speak_worker.start()
        self._update_buttons()

    def _stop_speaking(self) -> None:
        if not self.is_speaking:
            return

        self.speaker.stop()
        self.is_speaking = False
        self._update_buttons()

    def _update_emotion_detection(self, dt: float) -> None:
        if self._emotion_result is not None:
            self.current_emotion = self._emotion_result
            self._emotion_result = None

        if self._emotion_worker and self._emotion_worker.is_alive():
            return

        self._emotion_timer += dt
        if self._emotion_timer < EMOTION_DETECT_INTERVAL:
            return

        self._emotion_timer = 0.0
        frame = self.webcam.get_frame()
        if frame is None:
            return

        self._emotion_worker = threading.Thread(target=self._detect_emotion, args=(frame,), daemon=True)
        self._emotion_worker.start()

    def _detect_emotion(self, frame: np.ndarray) -> None:
        try:
            self._emotion_result = self.emotion_detector.detect(frame)
        except Exception:
            self._emotion_result = None

    def handle_event(self, event: pygame.event.Event) -> None:
        self.answer_box.handle_event(event)
        self.record_button.handle_event(event)
        self.prev_button.handle_event(event)
        self.next_button.handle_event(event)
        self.restart_button.handle_event(event)

    def update(self, dt: float) -> None:
        self.answer_box.update(dt)

        if self.is_speaking and self._speak_worker and not self._speak_worker.is_alive():
            self.is_speaking = False

        self._update_emotion_detection(dt)

        if self._transcribe_result is not None:
            index, text = self._transcribe_result
            self._transcribe_result = None
            if 0 <= index < len(self.answers):
                self.answers[index] = text
                if index == self.index:
                    self.answer_box.set_text(text)
            self.record_button.enabled = True
        elif self._transcribe_error and not (self._transcribe_worker and self._transcribe_worker.is_alive()):
            self.record_button.enabled = True

        self._update_buttons()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(c.BACKGROUND)

        if not self.questions:
            empty = self.question_font.render("No questions generated.", True, c.MUTED_TEXT)
            surface.blit(empty, empty.get_rect(center=(c.SCREEN_WIDTH // 2, c.SCREEN_HEIGHT // 2)))
        else:
            counter = self.counter_font.render(
                f"Question {self.index + 1} of {len(self.questions)}", True, c.MUTED_TEXT
            )
            surface.blit(counter, (60, 60))

            question = self.questions[self.index]
            y = 100
            max_question_width = self.webcam_rect.left - 60 - 20
            for line in wrap_text(question, self.question_font, max_question_width):
                rendered = self.question_font.render(line, True, c.TEXT)
                surface.blit(rendered, (60, y))
                y += self.question_font.get_linesize() + 6

            self.answer_box.draw(surface)
            self._draw_recording_status(surface)
            self._draw_webcam_preview(surface)

        self.record_button.draw(surface)
        self.prev_button.draw(surface)
        self.next_button.draw(surface)
        self.restart_button.draw(surface)

    def _draw_webcam_preview(self, surface: pygame.Surface) -> None:
        frame = self.webcam.get_frame()
        if frame is not None:
            rgb = np.ascontiguousarray(frame[:, :, ::-1].swapaxes(0, 1))
            preview = pygame.surfarray.make_surface(rgb)
            preview = pygame.transform.smoothscale(preview, self.webcam_rect.size)
            surface.blit(preview, self.webcam_rect)
        else:
            pygame.draw.rect(surface, c.PANEL, self.webcam_rect, border_radius=6)
            label = self.counter_font.render("Camera unavailable", True, c.MUTED_TEXT)
            surface.blit(label, label.get_rect(center=self.webcam_rect.center))

        pygame.draw.rect(surface, c.INPUT_BORDER, self.webcam_rect, width=2, border_radius=6)

        if self.current_emotion:
            text = f"{self.current_emotion['label'].title()} ({self.current_emotion['score']:.0%})"
            rendered = self.counter_font.render(text, True, c.MUTED_TEXT)
            surface.blit(rendered, rendered.get_rect(centerx=self.webcam_rect.centerx, top=self.webcam_rect.bottom + 6))

    def _draw_recording_status(self, surface: pygame.Surface) -> None:
        if self.is_recording:
            text, color = "Recording... click Stop Recording when finished.\nWARNING: THIS WILL OVERWRITE ANY TEXT", c.ERROR_TEXT
        elif self.is_speaking:
            text, color = "Reading question aloud...", c.MUTED_TEXT
        elif self._transcribe_worker and self._transcribe_worker.is_alive():
            text, color = "Transcribing your answer...", c.MUTED_TEXT
        elif self._transcribe_error:
            text, color = self._transcribe_error, c.ERROR_TEXT
        else:
            return

        lines = text.split("\n")
        line_height = self.counter_font.get_linesize()
        y = self.record_button.rect.top - line_height * len(lines) - 8
        for line in lines:
            rendered = self.counter_font.render(line, True, color)
            surface.blit(rendered, rendered.get_rect(centerx=c.SCREEN_WIDTH // 2, y=y))
            y += line_height

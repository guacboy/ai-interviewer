"""Resume input screen: paste/enter resume text and start question generation."""

import threading

import pygame

from question_generator import generate_questions
from resume_parser import load_resume

from .. import constants as c
from ..widgets import Button, TextBox
from .base import Screen

NUM_QUESTIONS = 5

#TODO: add upload pdf feature

class ResumeInputScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.label_font = pygame.font.SysFont(None, 28)
        self.status_font = pygame.font.SysFont(None, 24)
        button_font = pygame.font.SysFont(None, 32)

        self.text_box = TextBox(
            (60, 110, c.SCREEN_WIDTH - 120, c.SCREEN_HEIGHT - 240),
            pygame.font.SysFont(None, 24),
            placeholder="Paste your resume text here, or enter a path to a PDF/text file...",
        )

        self.generate_button = Button(
            (60, c.SCREEN_HEIGHT - 90, 220, 50),
            "Generate Questions",
            button_font,
            on_click=self._start_generation,
        )
        self.back_button = Button(
            (c.SCREEN_WIDTH - 60 - 140, c.SCREEN_HEIGHT - 90, 140, 50),
            "Back",
            button_font,
            on_click=lambda: app.switch_to("home"),
        )

        self._worker: threading.Thread | None = None
        self._result: tuple[str, list[str]] | None = None
        self._error: str | None = None

    def on_enter(self, **kwargs) -> None:
        self._error = None
        self._result = None
        self.generate_button.enabled = True

    def _start_generation(self) -> None:
        if self._worker and self._worker.is_alive():
            return

        source = self.text_box.text.strip()
        if not source:
            self._error = "Please paste your resume text or enter a file path."
            return

        self._error = None
        self.generate_button.enabled = False
        self._worker = threading.Thread(target=self._generate, args=(source,), daemon=True)
        self._worker.start()

    def _generate(self, source: str) -> None:
        try:
            resume_text = load_resume(source)
            questions = generate_questions(resume_text, num_questions=NUM_QUESTIONS)
        except Exception as exc:
            self._error = f"Failed to generate questions: {exc}"
            return

        self._result = (resume_text, questions)

    def handle_event(self, event: pygame.event.Event) -> None:
        self.text_box.handle_event(event)
        self.generate_button.handle_event(event)
        self.back_button.handle_event(event)

    def update(self, dt: float) -> None:
        self.text_box.update(dt)

        if self._result is not None:
            resume_text, questions = self._result
            self._result = None
            self.generate_button.enabled = True
            self.app.switch_to("questions", questions=questions, resume_text=resume_text)
        elif self._error:
            self.generate_button.enabled = True

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(c.BACKGROUND)

        label = self.label_font.render("Enter your resume", True, c.TEXT)
        surface.blit(label, (60, 60))

        self.text_box.draw(surface)

        is_generating = bool(self._worker and self._worker.is_alive())
        if is_generating:
            status_text, color = "Generating questions... this may take a minute.", c.MUTED_TEXT
        elif self._error:
            status_text, color = self._error, c.ERROR_TEXT
        else:
            status_text, color = "", c.MUTED_TEXT

        if status_text:
            status = self.status_font.render(status_text, True, color)
            surface.blit(status, (60, c.SCREEN_HEIGHT - 130))

        self.generate_button.draw(surface)
        self.back_button.draw(surface)

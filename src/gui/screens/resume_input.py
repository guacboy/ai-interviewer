"""Resume input screen: paste/enter resume text and start question generation."""

import threading
from pathlib import Path

import pygame

from question_generator import generate_questions
from resume_parser import load_resume

from .. import constants as c
from ..widgets import Button, TextBox
from .base import Screen

NUM_QUESTIONS = 5


class ResumeInputScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.status_font = pygame.font.SysFont(None, 24)
        self.divider_font = pygame.font.SysFont(None, 24)
        button_font = pygame.font.SysFont(None, 32)

        upload_width = 240
        self.upload_button = Button(
            ((c.SCREEN_WIDTH - upload_width) // 2, 70, upload_width, 50),
            "Upload Resume File",
            button_font,
            on_click=self._upload_file,
        )
        self._upload_status_y = 130

        self._divider_y = 185

        self.text_box = TextBox(
            (60, 210, c.SCREEN_WIDTH - 120, c.SCREEN_HEIGHT - 340),
            pygame.font.SysFont(None, 24),
            placeholder="Or paste your resume text here...",
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
        self._uploaded_path: str | None = None
        self._uploaded_name: str | None = None

    def on_enter(self, **kwargs) -> None:
        self._error = None
        self._result = None
        self._uploaded_path = None
        self._uploaded_name = None
        self.generate_button.enabled = True

    def _start_generation(self) -> None:
        if self._worker and self._worker.is_alive():
            return

        source = self.text_box.text.strip() or self._uploaded_path
        if not source:
            self._error = "Please paste your resume text or upload a file."
            return

        self._error = None
        self.generate_button.enabled = False
        self._worker = threading.Thread(target=self._generate, args=(source,), daemon=True)
        self._worker.start()

    def _upload_file(self) -> None:
        try:
            import tkinter as tk
            from tkinter import filedialog
        except ImportError:
            self._error = "File dialog is unavailable on this system."
            return

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            path = filedialog.askopenfilename(
                title="Select resume file",
                filetypes=[("Resume files", "*.pdf *.txt"), ("All files", "*.*")],
            )
        finally:
            root.destroy()

        if path:
            self._uploaded_path = path
            self._uploaded_name = Path(path).name

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
        self.upload_button.handle_event(event)
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

        self.upload_button.draw(surface)
        self._draw_upload_status(surface)
        self._draw_divider(surface)
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

    def _draw_upload_status(self, surface: pygame.Surface) -> None:
        if not self._uploaded_name:
            return

        check = self.status_font.render("✓", True, c.SUCCESS_TEXT)
        text = self.status_font.render(
            f"{self._uploaded_name} has been uploaded successfully.", True, c.SUCCESS_TEXT
        )

        total_width = check.get_width() + 8 + text.get_width()
        x = (c.SCREEN_WIDTH - total_width) // 2
        surface.blit(check, (x, self._upload_status_y))
        surface.blit(text, (x + check.get_width() + 8, self._upload_status_y))

    def _draw_divider(self, surface: pygame.Surface) -> None:
        label = self.divider_font.render("or", True, c.MUTED_TEXT)
        label_rect = label.get_rect(center=(c.SCREEN_WIDTH // 2, self._divider_y))

        margin, gap = 60, 16
        pygame.draw.line(
            surface, c.INPUT_BORDER, (margin, self._divider_y), (label_rect.left - gap, self._divider_y), 2
        )
        pygame.draw.line(
            surface, c.INPUT_BORDER, (label_rect.right + gap, self._divider_y), (c.SCREEN_WIDTH - margin, self._divider_y), 2
        )
        surface.blit(label, label_rect)

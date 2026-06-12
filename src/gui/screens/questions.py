"""Questions screen: displays generated interview questions with navigation."""

import pygame

from .. import constants as c
from ..widgets import Button, wrap_text
from .base import Screen

#TODO: remove temp prev and next btn, and replace with skip btn
#TODO: add an "interviewer" with the questions appearing on top as an overlay

class QuestionsScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.question_font = pygame.font.SysFont(None, 32)
        self.counter_font = pygame.font.SysFont(None, 22)
        button_font = pygame.font.SysFont(None, 32)

        self.questions: list[str] = []
        self.index = 0

        self.prev_button = Button((60, c.SCREEN_HEIGHT - 90, 140, 50), "Previous", button_font, on_click=self._prev)
        self.next_button = Button(
            (c.SCREEN_WIDTH - 200, c.SCREEN_HEIGHT - 90, 140, 50), "Next", button_font, on_click=self._next
        )
        self.restart_button = Button(
            ((c.SCREEN_WIDTH - 160) // 2, c.SCREEN_HEIGHT - 90, 160, 50),
            "New Resume",
            button_font,
            on_click=lambda: app.switch_to("resume_input"),
        )

    def on_enter(self, **kwargs) -> None:
        self.questions = kwargs.get("questions", [])
        self.index = 0
        self._update_buttons()

    def _prev(self) -> None:
        if self.index > 0:
            self.index -= 1
            self._update_buttons()

    def _next(self) -> None:
        if self.index < len(self.questions) - 1:
            self.index += 1
            self._update_buttons()

    def _update_buttons(self) -> None:
        self.prev_button.enabled = self.index > 0
        self.next_button.enabled = self.index < len(self.questions) - 1

    def handle_event(self, event: pygame.event.Event) -> None:
        self.prev_button.handle_event(event)
        self.next_button.handle_event(event)
        self.restart_button.handle_event(event)

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
            y = 140
            for line in wrap_text(question, self.question_font, c.SCREEN_WIDTH - 120):
                rendered = self.question_font.render(line, True, c.TEXT)
                surface.blit(rendered, (60, y))
                y += self.question_font.get_linesize() + 6

        self.prev_button.draw(surface)
        self.next_button.draw(surface)
        self.restart_button.draw(surface)

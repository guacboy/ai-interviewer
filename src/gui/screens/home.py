"""Home screen: welcome message and entry point into the interview flow."""

import pygame

from .. import constants as c
from ..widgets import Button
from .base import Screen


class HomeScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.title_font = pygame.font.SysFont(None, 64)
        self.subtitle_font = pygame.font.SysFont(None, 28)

        button_font = pygame.font.SysFont(None, 32)
        button_rect = ((c.SCREEN_WIDTH - 240) // 2, c.SCREEN_HEIGHT // 2 + 20, 240, 56)
        self.start_button = Button(
            button_rect,
            "Start Interview",
            button_font,
            on_click=lambda: app.switch_to("resume_input"),
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        self.start_button.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(c.BACKGROUND)

        title = self.title_font.render("AI Interviewer", True, c.TEXT)
        surface.blit(title, title.get_rect(centerx=c.SCREEN_WIDTH // 2, y=140))

        subtitle = self.subtitle_font.render(
            "Practice technical interviews tailored to your resume.", True, c.MUTED_TEXT
        )
        surface.blit(subtitle, subtitle.get_rect(centerx=c.SCREEN_WIDTH // 2, y=220))

        self.start_button.draw(surface)

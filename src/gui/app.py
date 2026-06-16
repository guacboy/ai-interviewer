"""Pygame application shell: window setup, main loop, and screen navigation."""

import pygame

from . import constants as c
from .screens.home import HomeScreen
from .screens.questions import QuestionsScreen
from .screens.results import ResultsScreen
from .screens.resume_input import ResumeInputScreen


class App:
    def __init__(self):
        pygame.init()

        self.surface = pygame.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        pygame.display.set_caption("AI Interviewer")

        try:
            pygame.scrap.init()
        except (pygame.error, AttributeError):
            pass
        self.clock = pygame.time.Clock()

        self.screens = {
            "home": HomeScreen(self),
            "resume_input": ResumeInputScreen(self),
            "questions": QuestionsScreen(self),
            "results": ResultsScreen(self),
        }
        self.current_name = "home"
        self.current = self.screens[self.current_name]
        self.current.on_enter()

    def switch_to(self, name: str, **kwargs) -> None:
        self.current_name = name
        self.current = self.screens[name]
        self.current.on_enter(**kwargs)

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(c.FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.current.handle_event(event)

            self.current.update(dt)
            self.current.draw(self.surface)
            pygame.display.flip()

        pygame.quit()

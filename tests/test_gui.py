import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from gui.widgets import wrap_text


@pytest.fixture(scope="module", autouse=True)
def _pygame_init():
    pygame.init()
    yield
    pygame.quit()


class TestWrapText:
    def test_short_line_is_not_wrapped(self):
        font = pygame.font.SysFont(None, 24)
        assert wrap_text("Hello world", font, 1000) == ["Hello world"]

    def test_long_line_wraps_on_word_boundaries(self):
        font = pygame.font.SysFont(None, 24)
        text = ("word " * 50).strip()
        max_width = font.size("word word word")[0]

        lines = wrap_text(text, font, max_width)

        assert len(lines) > 1
        for line in lines:
            assert font.size(line)[0] <= max_width

    def test_preserves_blank_lines(self):
        font = pygame.font.SysFont(None, 24)
        assert wrap_text("first\n\nsecond", font, 1000) == ["first", "", "second"]

    def test_empty_string_returns_single_empty_line(self):
        font = pygame.font.SysFont(None, 24)
        assert wrap_text("", font, 1000) == [""]


class TestAppNavigation:
    def test_switch_to_changes_current_screen(self):
        from gui.app import App

        app = App()

        assert app.current_name == "home"

        app.switch_to("resume_input")
        assert app.current_name == "resume_input"
        assert app.current is app.screens["resume_input"]

        app.switch_to("questions", questions=["Q1", "Q2"])
        assert app.current_name == "questions"
        assert app.current.questions == ["Q1", "Q2"]

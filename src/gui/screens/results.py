"""Results screen: detailed interview score report after the session ends."""

import threading
from collections import Counter

import pygame

from scorer import score_interview

from .. import constants as c
from ..widgets import Button, wrap_text
from .base import Screen

_SIDE_PAD = 40
_SCROLL_TOP = 188   # y where the per-question list starts
_SCROLL_BTM = 622   # y where it ends (leaves room for scroll hint)
_SCROLL_H = _SCROLL_BTM - _SCROLL_TOP  # 434
_CARD_H = 152        # height of each question card

#TODO(bug): fix overlapping information formatting
#TODO(feat): add progress bar

def _score_color(score: float) -> tuple:
    if score >= 8.0:
        return c.SUCCESS_TEXT
    if score >= 6.0:
        return c.ACCENT
    return c.ERROR_TEXT


class ResultsScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.title_font = pygame.font.SysFont(None, 42)
        self.score_font = pygame.font.SysFont(None, 52)
        self.body_font = pygame.font.SysFont(None, 24)
        self.label_font = pygame.font.SysFont(None, 22)
        button_font = pygame.font.SysFont(None, 28)

        self._questions: list[str] = []
        self._answers: list[str] = []
        self._emotion_history: list[dict | None] = []
        self._report: dict | None = None
        self._scoring = False
        self._score_error: str | None = None
        self._worker: threading.Thread | None = None
        self._scroll_y = 0

        self.start_over_button = Button(
            (c.SCREEN_WIDTH - 220, 14, 200, 44),
            "Start Over",
            button_font,
            on_click=self._start_over,
        )

    def on_enter(self, **kwargs) -> None:
        self._questions = kwargs.get("questions", [])
        self._answers = kwargs.get("answers", [])
        self._emotion_history = kwargs.get("emotion_history", [])
        self._report = None
        self._score_error = None
        self._scoring = True
        self._scroll_y = 0

        self._worker = threading.Thread(target=self._run_scoring, daemon=True)
        self._worker.start()

    def _run_scoring(self) -> None:
        try:
            self._report = score_interview(
                self._questions, self._answers, self._emotion_history
            )
        except Exception as exc:
            self._score_error = str(exc)
        finally:
            self._scoring = False

    def _start_over(self) -> None:
        self.app.switch_to("resume_input")

    def _max_scroll(self) -> int:
        return max(0, len(self._questions) * _CARD_H - _SCROLL_H)

    def handle_event(self, event: pygame.event.Event) -> None:
        self.start_over_button.handle_event(event)
        if event.type == pygame.MOUSEWHEEL and self._report:
            self._scroll_y = max(0, min(self._max_scroll(), self._scroll_y - event.y * 30))

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(c.BACKGROUND)
        self._draw_header(surface)

        if self._scoring:
            msg = self.body_font.render("Scoring your interview, please wait...", True, c.MUTED_TEXT)
            surface.blit(msg, msg.get_rect(center=(c.SCREEN_WIDTH // 2, c.SCREEN_HEIGHT // 2)))
        elif self._score_error:
            msg = self.body_font.render(f"Scoring failed: {self._score_error}", True, c.ERROR_TEXT)
            surface.blit(msg, msg.get_rect(center=(c.SCREEN_WIDTH // 2, c.SCREEN_HEIGHT // 2)))
        else:
            self._draw_report(surface)

        self.start_over_button.draw(surface)

    def _draw_header(self, surface: pygame.Surface) -> None:
        title = self.title_font.render("Interview Complete", True, c.TEXT)
        surface.blit(title, (40, 16))

    def _draw_report(self, surface: pygame.Surface) -> None:
        report = self._report

        # Overall score
        score_val = report["overall_score"]
        score_surf = self.score_font.render(f"{score_val:.1f} / 10", True, _score_color(score_val))
        surface.blit(score_surf, (40, 68))

        # Overall feedback
        y = 68 + self.score_font.get_linesize() + 4
        for line in wrap_text(report["overall_feedback"], self.body_font, c.SCREEN_WIDTH - 80):
            surface.blit(self.body_font.render(line, True, c.MUTED_TEXT), (40, y))
            y += self.body_font.get_linesize() + 2

        # Emotion summary
        emo_line = self._emotion_summary()
        surface.blit(self.label_font.render(emo_line, True, c.MUTED_TEXT), (40, y + 4))

        # Separator
        pygame.draw.line(surface, c.PANEL, (0, _SCROLL_TOP - 8), (c.SCREEN_WIDTH, _SCROLL_TOP - 8))

        # Scrollable question cards
        clip = surface.get_clip()
        surface.set_clip(pygame.Rect(0, _SCROLL_TOP, c.SCREEN_WIDTH, _SCROLL_H))

        q_scores = report.get("questions", [])
        for i, (question, answer, emotion) in enumerate(
            zip(self._questions, self._answers, self._emotion_history)
        ):
            card_y = _SCROLL_TOP + i * _CARD_H - self._scroll_y
            if card_y + _CARD_H < _SCROLL_TOP or card_y > _SCROLL_BTM:
                continue
            q_score = q_scores[i] if i < len(q_scores) else None
            self._draw_card(surface, card_y, i + 1, question, answer, emotion, q_score)

        surface.set_clip(clip)

        if self._max_scroll() > 0:
            hint = self.label_font.render("scroll to see all questions", True, c.MUTED_TEXT)
            surface.blit(hint, hint.get_rect(centerx=c.SCREEN_WIDTH // 2, bottom=c.SCREEN_HEIGHT - 6))

    def _draw_card(
        self,
        surface: pygame.Surface,
        y: int,
        number: int,
        question: str,
        answer: str,
        emotion: dict | None,
        q_score: dict | None,
    ) -> None:
        x = _SIDE_PAD
        w = c.SCREEN_WIDTH - 2 * _SIDE_PAD

        # Score badge (top-right of card)
        if q_score:
            score_val = q_score["score"]
            badge = self.body_font.render(f"{score_val:.1f}/10", True, _score_color(score_val))
            surface.blit(badge, (x + w - badge.get_width(), y + 8))
            line_end = x + w - badge.get_width() - 10
        else:
            line_end = x + w

        # "Q1 ─────" header
        q_label = self.body_font.render(f"Q{number}", True, c.ACCENT)
        surface.blit(q_label, (x, y + 8))
        line_start = x + q_label.get_width() + 8
        pygame.draw.line(surface, c.PANEL, (line_start, y + 18), (line_end, y + 18), 1)

        # Question text (1 line, truncated)
        surface.blit(
            self.label_font.render(self._clip(question, self.label_font, w), True, c.TEXT),
            (x + 4, y + 30),
        )

        # Answer excerpt (1 line)
        a_text = answer.strip() if answer.strip() else "(no answer given)"
        surface.blit(
            self.label_font.render(self._clip(f"Answer: {a_text}", self.label_font, w), True, c.MUTED_TEXT),
            (x + 4, y + 52),
        )

        # Feedback (up to 2 lines)
        if q_score:
            fb_y = y + 74
            for line in wrap_text(q_score["feedback"], self.label_font, w)[:2]:
                surface.blit(self.label_font.render(line, True, c.MUTED_TEXT), (x + 4, fb_y))
                fb_y += self.label_font.get_linesize() + 2

        # Emotion
        emo_str = (
            f"Emotion: {emotion['label'].title()} ({emotion['score']:.0%})"
            if emotion
            else "Emotion: not detected"
        )
        surface.blit(self.label_font.render(emo_str, True, c.MUTED_TEXT), (x + 4, y + 120))

        # Card bottom divider
        pygame.draw.line(surface, c.PANEL, (x, y + _CARD_H - 4), (x + w, y + _CARD_H - 4), 1)

    def _emotion_summary(self) -> str:
        detected = [e["label"].title() for e in self._emotion_history if e]
        if not detected:
            return "Emotion data: none captured"
        dominant, count = Counter(detected).most_common(1)[0]
        total = len(self._emotion_history)
        return f"Dominant emotion: {dominant} ({count}/{total} questions)"

    @staticmethod
    def _clip(text: str, font: pygame.font.Font, max_width: int) -> str:
        if font.size(text)[0] <= max_width:
            return text
        while text and font.size(text + "…")[0] > max_width:
            text = text[:-1]
        return text + "…"

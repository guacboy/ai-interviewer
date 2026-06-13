"""Reusable Pygame UI widgets: buttons, a multi-line text box, and text wrapping."""

import pygame

from . import constants as c


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Word-wrap `text` to fit within `max_width` pixels, preserving newlines."""
    lines: list[str] = []
    for raw_line in text.split("\n"):
        if not raw_line:
            lines.append("")
            continue

        current = ""
        for word in raw_line.split(" "):
            candidate = word if not current else f"{current} {word}"
            if font.size(candidate)[0] <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)

    return lines


class Button:
    """A clickable rectangular button with hover and enabled/disabled states."""

    def __init__(self, rect, text: str, font: pygame.font.Font, on_click=None, enabled: bool = True):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.on_click = on_click
        self.enabled = enabled
        self.hovered = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.enabled:
            return

        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.on_click:
                self.on_click()

    def draw(self, surface: pygame.Surface) -> None:
        if not self.enabled:
            color, text_color = c.PANEL, c.MUTED_TEXT
        elif self.hovered:
            color, text_color = c.ACCENT_HOVER, c.WIDGET_TEXT
        else:
            color, text_color = c.ACCENT, c.WIDGET_TEXT

        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        label = self.font.render(self.text, True, text_color)
        surface.blit(label, label.get_rect(center=self.rect.center))


class TextBox:
    """A multi-line, word-wrapped, scrollable text input box."""

    def __init__(self, rect, font: pygame.font.Font, placeholder: str = ""):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.placeholder = placeholder
        self.text = ""
        self.active = False
        self.scroll = 0
        self._blink_timer = 0.0
        self._show_cursor = True
        self._padding = 10
        self._line_height = font.get_linesize()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
            self._scroll_by(-event.y)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.text += "\n"
            elif event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL):
                self._paste()
            else:
                self.text += event.unicode
            self._scroll_to_bottom()

    def set_text(self, text: str) -> None:
        self.text = text
        self._scroll_to_bottom()

    def _paste(self) -> None:
        try:
            data = pygame.scrap.get(pygame.SCRAP_TEXT)
        except (pygame.error, AttributeError):
            return

        if data:
            self.text += data.decode("utf-8", errors="ignore").replace("\x00", "")

    def _wrapped_lines(self) -> list[str]:
        max_width = self.rect.width - 2 * self._padding
        return wrap_text(self.text, self.font, max_width)

    def _visible_line_count(self) -> int:
        return max(1, (self.rect.height - 2 * self._padding) // self._line_height)

    def _scroll_by(self, amount: int) -> None:
        max_scroll = max(0, len(self._wrapped_lines()) - self._visible_line_count())
        self.scroll = max(0, min(max_scroll, self.scroll + amount))

    def _scroll_to_bottom(self) -> None:
        max_scroll = max(0, len(self._wrapped_lines()) - self._visible_line_count())
        self.scroll = max_scroll

    def update(self, dt: float) -> None:
        self._blink_timer += dt
        if self._blink_timer >= 0.5:
            self._blink_timer = 0.0
            self._show_cursor = not self._show_cursor

    def draw(self, surface: pygame.Surface) -> None:
        border_color = c.INPUT_BORDER_ACTIVE if self.active else c.INPUT_BORDER
        pygame.draw.rect(surface, c.INPUT_BG, self.rect, border_radius=6)
        pygame.draw.rect(surface, border_color, self.rect, width=2, border_radius=6)

        clip = surface.get_clip()
        surface.set_clip(self.rect)

        if not self.text and not self.active:
            placeholder = self.font.render(self.placeholder, True, c.WIDGET_MUTED_TEXT)
            surface.blit(placeholder, (self.rect.x + self._padding, self.rect.y + self._padding))
        else:
            lines = self._wrapped_lines()
            visible = lines[self.scroll : self.scroll + self._visible_line_count()]
            y = self.rect.y + self._padding
            for line in visible:
                rendered = self.font.render(line, True, c.WIDGET_TEXT)
                surface.blit(rendered, (self.rect.x + self._padding, y))
                y += self._line_height

            if self.active and self._show_cursor and visible:
                last_line = visible[-1]
                cursor_x = self.rect.x + self._padding + self.font.size(last_line)[0]
                cursor_y = self.rect.y + self._padding + (len(visible) - 1) * self._line_height
                pygame.draw.line(
                    surface, c.WIDGET_TEXT, (cursor_x, cursor_y), (cursor_x, cursor_y + self._line_height), 2
                )

        surface.set_clip(clip)

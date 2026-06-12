"""Base class for GUI screens managed by `gui.app.App`."""

import pygame


class Screen:
    """A single screen in the app. Subclasses override the hooks they need."""

    def __init__(self, app):
        self.app = app

    def on_enter(self, **kwargs) -> None:
        """Called whenever this screen becomes the active screen."""

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle a single Pygame event."""

    def update(self, dt: float) -> None:
        """Advance any time-based state. `dt` is the elapsed time in seconds."""

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the screen onto `surface`."""

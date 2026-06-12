"""Entry point for the AI Interviewer Pygame app."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from gui.app import App


def main() -> None:
    App().run()


if __name__ == "__main__":
    main()

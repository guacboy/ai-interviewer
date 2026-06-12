"""CLI demo: extract resume text from a PDF, a text file, or pasted text.

Usage:
    python scripts/parse_resume.py path/to/resume.pdf
    python scripts/parse_resume.py "Pasted resume text goes here..."
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from resume_parser import load_resume


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Path to a PDF/text resume, or raw pasted text")
    args = parser.parse_args()

    text = load_resume(args.source)
    print(text)


if __name__ == "__main__":
    main()

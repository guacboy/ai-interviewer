"""CLI demo: generate interview questions from a resume.

Usage:
    python scripts/generate_questions.py path/to/resume.pdf
    python scripts/generate_questions.py "Pasted resume text..." --num-questions 3
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from question_generator import DEFAULT_MODEL, generate_questions
from resume_parser import load_resume


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Path to a PDF/text resume, or raw pasted text")
    parser.add_argument("--num-questions", type=int, default=5)
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Hugging Face model name")
    args = parser.parse_args()

    resume_text = load_resume(args.source)
    questions = generate_questions(
        resume_text,
        num_questions=args.num_questions,
        model_name=args.model,
    )
    for i, question in enumerate(questions, 1):
        print(f"{i}. {question}")


if __name__ == "__main__":
    main()

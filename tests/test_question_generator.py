from question_generator import build_messages, parse_questions


class TestBuildMessages:
    def test_returns_system_and_user_messages(self):
        messages = build_messages("Resume text")
        assert [m["role"] for m in messages] == ["system", "user"]

    def test_includes_resume_text_in_user_message(self):
        messages = build_messages("Jane Doe - Data Scientist")
        assert "Jane Doe - Data Scientist" in messages[1]["content"]

    def test_includes_num_questions_in_user_message(self):
        messages = build_messages("Resume text", num_questions=3)
        assert "3" in messages[1]["content"]

    def test_default_num_questions_is_five(self):
        messages = build_messages("Resume text")
        assert "5" in messages[1]["content"]


class TestParseQuestions:
    def test_numbered_with_periods(self):
        text = "1. What is your experience with Python?\n2. Describe a challenging project."
        assert parse_questions(text) == [
            "What is your experience with Python?",
            "Describe a challenging project.",
        ]

    def test_numbered_with_parentheses(self):
        text = "1) First question\n2) Second question"
        assert parse_questions(text) == ["First question", "Second question"]

    def test_bulleted_list(self):
        text = "- First question\n* Second question"
        assert parse_questions(text) == ["First question", "Second question"]

    def test_skips_blank_lines(self):
        text = "1. First question\n\n2. Second question\n"
        assert parse_questions(text) == ["First question", "Second question"]

    def test_strips_surrounding_whitespace(self):
        text = "  1.   First question   \n2.Second question"
        assert parse_questions(text) == ["First question", "Second question"]

    def test_plain_lines_without_list_markers(self):
        text = "First question\nSecond question"
        assert parse_questions(text) == ["First question", "Second question"]

    def test_empty_input_returns_empty_list(self):
        assert parse_questions("") == []

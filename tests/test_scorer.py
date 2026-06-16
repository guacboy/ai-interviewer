import pytest

from scorer import build_messages, parse_report, score_interview


class TestBuildMessages:
    def test_includes_all_questions_and_answers(self):
        messages = build_messages(
            ["What is Python?", "Describe OOP."],
            ["Python is a language.", "OOP uses classes."],
            [None, None],
        )
        user = messages[1]["content"]
        assert "What is Python?" in user
        assert "Python is a language." in user
        assert "Describe OOP." in user
        assert "OOP uses classes." in user

    def test_formats_detected_emotion(self):
        messages = build_messages(["Q?"], ["A."], [{"label": "nervous", "score": 0.72}])
        assert "Nervous (72%)" in messages[1]["content"]

    def test_missing_emotion_shows_not_detected(self):
        messages = build_messages(["Q?"], ["A."], [None])
        assert "not detected" in messages[1]["content"]

    def test_empty_answer_replaced_with_placeholder(self):
        messages = build_messages(["Q?"], ["   "], [None])
        assert "(no answer given)" in messages[1]["content"]

    def test_system_message_is_first(self):
        messages = build_messages(["Q?"], ["A."], [None])
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"


class TestParseReport:
    _VALID = '{"overall_score": 7.5, "overall_feedback": "Good.", "questions": [{"score": 8.0, "feedback": "Clear."}]}'

    def test_parses_valid_json(self):
        result = parse_report(self._VALID)
        assert result["overall_score"] == 7.5
        assert result["questions"][0]["score"] == 8.0

    def test_strips_markdown_fences(self):
        raw = f"```json\n{self._VALID}\n```"
        result = parse_report(raw)
        assert result["overall_score"] == 7.5

    def test_extracts_json_from_surrounding_text(self):
        raw = f"Here is the result:\n{self._VALID}\nEnd."
        result = parse_report(raw)
        assert result["overall_score"] == 7.5

    def test_raises_when_no_json(self):
        with pytest.raises(Exception):
            parse_report("No JSON here.")


class TestScoreInterview:
    _REPORT = '{"overall_score": 8.0, "overall_feedback": "Great.", "questions": [{"score": 8.0, "feedback": "Good."}]}'

    def test_calls_generate_fn_with_messages(self):
        calls = []

        def fake_generate(messages):
            calls.append(messages)
            return self._REPORT

        score_interview(["Q?"], ["A."], [None], generate_fn=fake_generate)
        assert len(calls) == 1
        assert isinstance(calls[0], list)

    def test_returns_parsed_report(self):
        result = score_interview(["Q?"], ["A."], [None], generate_fn=lambda m: self._REPORT)
        assert result["overall_score"] == 8.0
        assert "overall_feedback" in result
        assert isinstance(result["questions"], list)

    def test_passes_emotion_data_in_messages(self):
        captured = []

        def fake_generate(messages):
            captured.append(messages[1]["content"])
            return self._REPORT

        score_interview(["Q?"], ["A."], [{"label": "happy", "score": 0.9}], generate_fn=fake_generate)
        assert "Happy (90%)" in captured[0]

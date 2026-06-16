"""Score interview answers using the local LLM, incorporating emotion data."""

import json
import re

DEFAULT_MODEL = "microsoft/Phi-3.5-mini-instruct"

_SYSTEM_PROMPT = (
    "You are an expert interview evaluator. "
    "Score each candidate answer for relevance, depth, and clarity. "
    "Where provided, factor in the candidate's apparent emotional state. "
    "Respond with ONLY valid JSON - no markdown, no commentary outside the JSON object."
)

_RESPONSE_SCHEMA = """{
  "overall_score": <number 0.0-10.0>,
  "overall_feedback": "<2-3 sentence overall assessment>",
  "questions": [
    {"score": <number 0.0-10.0>, "feedback": "<1-2 sentence feedback for this answer>"},
    ...one entry per question...
  ]
}"""


def build_messages(
    questions: list[str],
    answers: list[str],
    emotion_history: list[dict | None],
) -> list[dict[str, str]]:
    """Build the chat messages for the scoring LLM call."""
    lines: list[str] = []
    for i, (q, a, emo) in enumerate(zip(questions, answers, emotion_history), 1):
        emo_str = f"{emo['label'].title()} ({emo['score']:.0%})" if emo else "not detected"
        a_str = a.strip() if a.strip() else "(no answer given)"
        lines += [
            f"{i}. Question: {q}",
            f"   Answer: {a_str}",
            f"   Emotion during answer: {emo_str}",
            "",
        ]

    user_prompt = (
        "Evaluate the following interview Q&A:\n\n"
        + "\n".join(lines)
        + f"\n\nRespond with JSON in this exact format:\n{_RESPONSE_SCHEMA}"
    )
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def parse_report(text: str) -> dict:
    """Extract and parse the JSON score report from raw LLM output."""
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in LLM response")
    return json.loads(text[start:end])


def score_interview(
    questions: list[str],
    answers: list[str],
    emotion_history: list[dict | None],
    model_name: str = DEFAULT_MODEL,
    generate_fn=None,
) -> dict:
    """Return a score report: {overall_score, overall_feedback, questions: [{score, feedback}]}."""
    if generate_fn is None:
        generate_fn = _make_generate_fn(model_name)

    messages = build_messages(questions, answers, emotion_history)
    return parse_report(generate_fn(messages))


def _make_generate_fn(model_name: str):
    def generate(messages: list[dict[str, str]]) -> str:
        from question_generator import _load_model

        tokenizer, model = _load_model(model_name)
        inputs = tokenizer.apply_chat_template(
            messages,
            return_tensors="pt",
            return_dict=True,
            add_generation_prompt=True,
        ).to(model.device)
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
        input_length = inputs["input_ids"].shape[-1]
        return tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True)

    return generate

"""Generate interview questions from resume text using a local Hugging Face LLM."""

import re

DEFAULT_MODEL = "microsoft/Phi-3.5-mini-instruct"

_SYSTEM_PROMPT = (
    "You are an experienced technical interviewer. Given a candidate's resume, "
    "generate interview questions tailored to their specific skills, experience, "
    "and projects. Mix behavioral and technical questions. "
    "Respond with ONLY a numbered list of questions, one per line, and no other text."
)

_LIST_PREFIX_RE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s*")


def build_messages(resume_text: str, num_questions: int = 5) -> list[dict[str, str]]:
    """Build the chat messages sent to the LLM for question generation."""
    user_prompt = (
        f"Resume:\n{resume_text}\n\n"
        f"Generate {num_questions} interview questions based on this resume."
    )
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def parse_questions(generated_text: str) -> list[str]:
    """Parse numbered/bulleted question lines out of the LLM's raw output."""
    questions = []
    for line in generated_text.splitlines():
        line = _LIST_PREFIX_RE.sub("", line).strip()
        if line:
            questions.append(line)
            
    return questions


_tokenizer = None
_model = None
_model_name = None


def _load_model(model_name: str = DEFAULT_MODEL):
    """Load (and cache) the tokenizer and model for `model_name`."""
    global _tokenizer, _model, _model_name
    
    if _model is None or _model_name != model_name:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        _model_name = model_name
        
    return _tokenizer, _model


def generate_questions(
    resume_text: str,
    num_questions: int = 5,
    model_name: str = DEFAULT_MODEL,
) -> list[str]:
    """Generate interview questions tailored to the given resume text."""
    tokenizer, model = _load_model(model_name)

    messages = build_messages(resume_text, num_questions)
    inputs = tokenizer.apply_chat_template(
        messages,
        return_tensors="pt",
        return_dict=True,
        add_generation_prompt=True,
    ).to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=512,
        do_sample=True,
        temperature=0.7,
        pad_token_id=tokenizer.eos_token_id,
    )

    input_length = inputs["input_ids"].shape[-1]
    generated = tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True)

    return parse_questions(generated)

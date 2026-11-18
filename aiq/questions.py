"""Load the evaluation questions. The file may be a plain list or {"questions": [...]}."""

import json

from aiq.config import QUESTIONS_FILE


def load_questions():
    data = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    return data["questions"] if isinstance(data, dict) and "questions" in data else data

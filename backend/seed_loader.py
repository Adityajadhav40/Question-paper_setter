import json
from pathlib import Path
from typing import List


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "questions_seed.json"


def load_seed_questions() -> List[dict]:
    if not DATA_FILE.exists():
        return []

    with DATA_FILE.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if isinstance(payload, dict):
        return payload.get("questions", [])
    return payload

from difflib import SequenceMatcher
from typing import List, Tuple

from .models import Question


def similarity_score(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def find_similar_questions(target: Question, candidates: List[Question], threshold: float = 0.72) -> List[Tuple[Question, float]]:
    matches = []
    for candidate in candidates:
        if candidate.id == target.id:
            continue
        score = similarity_score(target.question, candidate.question)
        if score >= threshold:
            matches.append((candidate, score))
    matches.sort(key=lambda item: item[1], reverse=True)
    return matches

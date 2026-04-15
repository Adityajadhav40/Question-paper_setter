from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from .ml_model import predictor
from .models import GeneratedPaper, GeneratedPaperQuestion, Question


DEFAULT_INSTRUCTIONS = (
    "Read all questions carefully. Attempt all compulsory questions and maintain neat working "
    "for analytical or descriptive answers."
)

SUBJECT_ALIASES = {
    "dbms": {"dbms", "database management systems"},
    "database management systems": {"dbms", "database management systems"},
    "os": {"os", "operating systems"},
    "operating systems": {"os", "operating systems"},
    "ml": {"ml", "machine learning"},
    "machine learning": {"ml", "machine learning"},
    "oop": {"oop", "object oriented programming", "object-oriented programming"},
    "object oriented programming": {"oop", "object oriented programming", "object-oriented programming"},
    "cn": {"cn", "computer networks"},
    "computer networks": {"cn", "computer networks"},
}

TYPE_VERBS = {
    "MCQ": "identify the most appropriate option for",
    "Short": "explain briefly",
    "Long": "discuss in depth",
}

BLOOM_BY_DIFFICULTY = {
    "Easy": "Remember",
    "Medium": "Apply",
    "Hard": "Analyze",
}


def _target_distribution(total_marks: int) -> Dict[str, int]:
    easy_marks = round(total_marks * 0.30)
    medium_marks = round(total_marks * 0.50)
    hard_marks = total_marks - easy_marks - medium_marks
    return {"Easy": easy_marks, "Medium": medium_marks, "Hard": hard_marks}


def _default_type_targets(total_marks: int, question_types: Sequence[str], blueprint: Optional[Dict[str, int]] = None) -> Dict[str, int]:
    if blueprint:
        return {key: int(value) for key, value in blueprint.items() if key in {"MCQ", "Short", "Long"}}
    active_types = list(question_types) if question_types else ["MCQ", "Short", "Long"]
    targets = {"MCQ": 0, "Short": 0, "Long": 0}
    if "MCQ" in active_types:
        targets["MCQ"] = max(0, round(total_marks * 0.20))
    if "Short" in active_types:
        targets["Short"] = max(0, round(total_marks * 0.30))
    assigned = targets["MCQ"] + targets["Short"]
    remaining = total_marks - assigned
    if "Long" in active_types:
        targets["Long"] = max(0, remaining)
    else:
        spill = remaining
        if "Short" in active_types:
            targets["Short"] += spill
        elif "MCQ" in active_types:
            targets["MCQ"] += spill
    return targets


def _normalize_label(value: Optional[str]) -> str:
    return " ".join((value or "").strip().lower().split())


def _subject_names(subject: str) -> set:
    normalized = _normalize_label(subject)
    aliases = set(SUBJECT_ALIASES.get(normalized, {normalized}))
    aliases.add(normalized)
    return aliases


def _matches_subject(question: Question, subject_names: set) -> bool:
    return _normalize_label(question.subject) in subject_names


def _matches_value(question_value: Optional[str], requested_value: Optional[str], all_token: str) -> bool:
    if not requested_value or requested_value == all_token:
        return True
    return _normalize_label(question_value) == _normalize_label(requested_value)


def _pick_reference_value(
    questions: Sequence[Question],
    requested_value: str,
    all_token: str,
    attribute: str,
    fallback: str,
) -> str:
    if requested_value != all_token:
        return requested_value
    values = [getattr(question, attribute, None) for question in questions if getattr(question, attribute, None)]
    if not values:
        return fallback
    return Counter(values).most_common(1)[0][0]


def _build_question_text(
    department: str,
    subject: str,
    topic: str,
    subtopic: str,
    difficulty: str,
    question_type: str,
    marks: int,
    variant_number: int,
) -> Tuple[str, str]:
    topic_text = subtopic if subtopic != "All Subtopics" else topic
    topic_text = topic_text if topic_text != "All Topics" else "core concepts"
    verb = TYPE_VERBS.get(question_type, "explain")
    if question_type == "MCQ":
        question = (
            f"[Auto] For {subject} in {department}, {verb} {topic_text}. "
            f"Variant {variant_number}: Which option best addresses this {difficulty.lower()} {marks}-mark prompt?"
        )
    elif question_type == "Short":
        question = (
            f"[Auto] In {subject}, {verb} {topic_text}. "
            f"Variant {variant_number}: Write a focused {difficulty.lower()} answer worth {marks} marks."
        )
    else:
        question = (
            f"[Auto] In {subject}, {verb} {topic_text} with a structured and well-reasoned response. "
            f"Variant {variant_number}: Prepare a {difficulty.lower()} answer for {marks} marks."
        )
    answer = (
        f"Expected answer should cover the key idea of {topic_text}, relate it to {subject}, "
        f"and match the depth expected for a {difficulty.lower()} {question_type.lower()} question."
    )
    return question, answer


def _filter_questions(
    questions: Sequence[Question],
    subject_names: set,
    topic: str,
    subtopic: str,
    semester: Optional[int],
    question_types: Sequence[str],
    strict_topic: bool,
    strict_subtopic: bool,
    strict_semester: bool,
) -> List[Question]:
    filtered: List[Question] = []
    for question in questions:
        if not _matches_subject(question, subject_names):
            continue
        if strict_topic and not _matches_value(question.topic, topic, "All Topics"):
            continue
        if strict_subtopic and not _matches_value(question.subtopic, subtopic, "All Subtopics"):
            continue
        if strict_semester and semester is not None and question.semester not in {semester, None}:
            continue
        if question_types and question.type not in question_types:
            continue
        filtered.append(question)
    return filtered


def _resolve_candidate_pool(
    db: Session,
    department: str,
    subject: str,
    topic: str,
    subtopic: str,
    semester: Optional[int],
    question_types: Sequence[str],
) -> Tuple[List[Question], List[str]]:
    department_questions = db.query(Question).filter(Question.department.ilike(department)).all()
    subject_names = _subject_names(subject)
    plans = [
        ("exact filters", True, True, True),
        ("semester relaxed", True, True, False),
        ("subtopic relaxed", True, False, False),
        ("topic relaxed", False, False, False),
    ]

    for label, strict_topic, strict_subtopic, strict_semester in plans:
        candidates = _filter_questions(
            questions=department_questions,
            subject_names=subject_names,
            topic=topic,
            subtopic=subtopic,
            semester=semester,
            question_types=question_types,
            strict_topic=strict_topic,
            strict_subtopic=strict_subtopic,
            strict_semester=strict_semester,
        )
        if candidates:
            notes = [f"Candidate pool resolved using {label}."]
            if not strict_semester and semester is not None:
                notes.append("Semester was relaxed to reuse the strongest subject-aligned questions.")
            if not strict_subtopic and subtopic != "All Subtopics":
                notes.append("Subtopic was relaxed to include nearby topic coverage.")
            if not strict_topic and topic != "All Topics":
                notes.append("Topic was relaxed to include the full subject bank.")
            return candidates, notes

    return [], ["No existing questions matched the current department and subject filter."]


def _ensure_support_questions(
    db: Session,
    questions: Sequence[Question],
    department: str,
    subject: str,
    topic: str,
    subtopic: str,
    requested_difficulty: str,
    question_types: Sequence[str],
    semester: Optional[int],
    total_marks: int,
    variant_count: int,
) -> List[Question]:
    active_types = list(question_types) if question_types else ["MCQ", "Short", "Long"]
    active_difficulties = [requested_difficulty] if requested_difficulty != "Mixed" else ["Easy", "Medium", "Hard"]
    target_topic = _pick_reference_value(questions, topic, "All Topics", "topic", "Core Concepts")
    topic_questions = [question for question in questions if _normalize_label(question.topic) == _normalize_label(target_topic)]
    target_subtopic = _pick_reference_value(topic_questions or questions, subtopic, "All Subtopics", "subtopic", "Fundamentals")
    target_semester = semester if semester is not None else next((question.semester for question in questions if question.semester), 5)
    required_count = max(variant_count + 1, 3)
    support_marks = sorted({1, 2, 3, 4, 5, 6, 8, 10, min(total_marks, 12), total_marks})
    existing_by_key = Counter(
        (
            question.type,
            question.difficulty,
            question.marks,
            _normalize_label(question.topic),
            _normalize_label(question.subtopic),
            question.semester,
        )
        for question in questions
    )
    created: List[Question] = []

    for question_type in active_types:
        for difficulty in active_difficulties:
            for marks in support_marks:
                key = (
                    question_type,
                    difficulty,
                    marks,
                    _normalize_label(target_topic),
                    _normalize_label(target_subtopic),
                    target_semester,
                )
                existing_count = existing_by_key.get(key, 0)
                if existing_count >= required_count:
                    continue

                for variant_number in range(existing_count + 1, required_count + 1):
                    question_text, answer_text = _build_question_text(
                        department=department,
                        subject=subject,
                        topic=target_topic,
                        subtopic=target_subtopic,
                        difficulty=difficulty,
                        question_type=question_type,
                        marks=marks,
                        variant_number=variant_number,
                    )
                    created.append(
                        Question(
                            department=department,
                            subject=subject,
                            topic=target_topic,
                            subtopic=target_subtopic,
                            question=question_text,
                            answer=answer_text,
                            difficulty=difficulty,
                            marks=marks,
                            type=question_type,
                            bloom_level=BLOOM_BY_DIFFICULTY[difficulty],
                            semester=target_semester,
                            course_outcome="CO-AUTO",
                            source_name="Auto Coverage Builder",
                            source_url="local://auto-coverage",
                            is_verified=True,
                            approval_status="approved",
                            quality_score=72,
                            times_used=0,
                        )
                    )
                    existing_by_key[key] += 1

    if created:
        db.add_all(created)
        db.flush()
    return created


def _question_score(
    question: Question,
    department: str,
    subject: str,
    topic: Optional[str],
    subtopic: Optional[str],
    requested_difficulty: str,
    question_types: Sequence[str],
) -> float:
    predicted_difficulty = predictor.predict_difficulty(question)
    score = 0.0

    if question.department.lower() == department.lower():
        score += 8
    if question.subject.lower() == subject.lower():
        score += 8
    if topic and topic != "All Topics" and question.topic.lower() == topic.lower():
        score += 6
    if subtopic and subtopic != "All Subtopics" and question.subtopic.lower() == subtopic.lower():
        score += 6
    if requested_difficulty != "Mixed" and question.difficulty == requested_difficulty:
        score += 5
    if predicted_difficulty == question.difficulty:
        score += 3
    if requested_difficulty != "Mixed" and predicted_difficulty == requested_difficulty:
        score += 2
    if question_types and question.type in question_types:
        score += 4
    score += max(0, question.quality_score or 0) / 25
    score -= min(question.times_used or 0, 12) * 1.2
    if question.is_verified:
        score += 2
    return score


def _find_exact_combinations(
    pool: List[Question],
    target_marks: int,
    excluded_ids: set,
    limit: int = 25,
) -> List[List[Question]]:
    if target_marks <= 0:
        return [[]]

    available = [question for question in pool if question.id not in excluded_ids]
    available.sort(key=lambda item: (-item.selection_score, -item.marks, item.id))
    solutions: List[List[Question]] = []
    current: List[Question] = []

    def backtrack(index: int, running_total: int) -> None:
        if len(solutions) >= limit:
            return
        if running_total == target_marks:
            solutions.append(list(current))
            return
        if running_total > target_marks or index >= len(available):
            return

        for next_index in range(index, len(available)):
            question = available[next_index]
            current.append(question)
            backtrack(next_index + 1, running_total + question.marks)
            current.pop()

    backtrack(0, 0)
    return solutions


def _pick_best_solution(
    solutions: List[List[Question]],
    prior_signatures: set,
    preferred_exclusions: set,
) -> Optional[List[Question]]:
    ranked = sorted(
        solutions,
        key=lambda combo: (
            len({question.id for question in combo} & preferred_exclusions),
            len(combo),
            -sum(question.selection_score for question in combo),
            len({question.subtopic for question in combo}),
            [question.id for question in combo],
        ),
    )
    for combo in ranked:
        signature = tuple(sorted(question.id for question in combo))
        if signature not in prior_signatures:
            prior_signatures.add(signature)
            return combo
    return ranked[0] if ranked else None


def _select_by_type_targets(
    questions: List[Question],
    type_targets: Dict[str, int],
    prior_signatures: set,
    previous_variant_ids: set,
) -> Tuple[List[Question], int]:
    selected: List[Question] = []
    used_ids: set = set()

    for question_type, marks in type_targets.items():
        if marks <= 0:
            continue
        type_pool = [question for question in questions if question.type == question_type]
        combos = _find_exact_combinations(type_pool, marks, used_ids)
        chosen = _pick_best_solution(combos, set(), previous_variant_ids)
        if chosen:
            selected.extend(chosen)
            used_ids.update(question.id for question in chosen)

    total = sum(question.marks for question in selected)
    return selected, total


def _select_by_difficulty_targets(
    questions: List[Question],
    total_marks: int,
    prior_signatures: set,
    previous_variant_ids: set,
) -> Tuple[List[Question], int]:
    selected: List[Question] = []
    used_ids: set = set()
    difficulty_targets = _target_distribution(total_marks)

    for difficulty, marks in difficulty_targets.items():
        pool = [question for question in questions if question.difficulty == difficulty]
        combos = _find_exact_combinations(pool, marks, used_ids)
        chosen = _pick_best_solution(combos, set(), previous_variant_ids)
        if chosen:
            selected.extend(chosen)
            used_ids.update(question.id for question in chosen)

    total = sum(question.marks for question in selected)
    return selected, total


def _complete_to_total(
    questions: List[Question],
    selected: List[Question],
    total_marks: int,
    prior_signatures: set,
    previous_variant_ids: set,
) -> List[Question]:
    current_total = sum(question.marks for question in selected)
    if current_total == total_marks:
        return selected

    used_ids = {question.id for question in selected}
    remaining = total_marks - current_total
    combos = _find_exact_combinations(questions, remaining, used_ids)
    chosen = _pick_best_solution(combos, set(), previous_variant_ids)
    if chosen:
        return selected + chosen

    exact_all = _find_exact_combinations(questions, total_marks, set())
    exact_all_choice = _pick_best_solution(exact_all, prior_signatures, previous_variant_ids)
    if exact_all_choice:
        return exact_all_choice

    raise ValueError(
        f"Could not generate an exact {total_marks}-mark paper with the selected filters. "
        f"Try All Topics, All Subtopics, more question types, or fewer variants."
    )


def _build_variant(
    questions: List[Question],
    total_marks: int,
    requested_difficulty: str,
    question_types: Sequence[str],
    prior_signatures: set,
    previous_variant_ids: set,
    blueprint: Optional[Dict[str, int]] = None,
) -> List[Question]:
    if requested_difficulty != "Mixed":
        difficulty_questions = [question for question in questions if question.difficulty == requested_difficulty]
        exact = _find_exact_combinations(difficulty_questions, total_marks, set())
        chosen = _pick_best_solution(exact, prior_signatures, previous_variant_ids)
        if not chosen:
            raise ValueError(f"Unable to create an exact {requested_difficulty} paper of {total_marks} marks.")
        return chosen

    type_targets = _default_type_targets(total_marks, question_types, blueprint)
    type_selected, type_total = _select_by_type_targets(questions, type_targets, prior_signatures, previous_variant_ids)

    if type_total == total_marks:
        return type_selected

    difficulty_selected, _ = _select_by_difficulty_targets(questions, total_marks, prior_signatures, previous_variant_ids)
    candidate = type_selected if sum(question.selection_score for question in type_selected) >= sum(
        question.selection_score for question in difficulty_selected
    ) else difficulty_selected

    completed = _complete_to_total(questions, candidate, total_marks, prior_signatures, previous_variant_ids)
    signature = tuple(sorted(question.id for question in completed))
    prior_signatures.add(signature)
    return completed


def _serialize_variant(questions: List[Question], variant_number: int, total_marks: int) -> Dict[str, object]:
    ordered = sorted(questions, key=lambda item: (item.type, item.difficulty, item.marks, item.id))
    return {
        "variant_number": variant_number,
        "question_count": len(ordered),
        "total_marks": total_marks,
        "difficulty_distribution": dict(Counter(question.difficulty for question in ordered)),
        "type_distribution": dict(Counter(question.type for question in ordered)),
        "questions": [
            {
                "id": question.id,
                "question": question.question,
                "answer": question.answer,
                "department": question.department,
                "subject": question.subject,
                "topic": question.topic,
                "subtopic": question.subtopic,
                "difficulty": question.difficulty,
                "marks": question.marks,
                "type": question.type,
                "bloom_level": question.bloom_level,
                "semester": question.semester,
                "course_outcome": question.course_outcome,
                "predicted_difficulty": predictor.predict_difficulty(question),
                "source_name": question.source_name,
                "source_url": question.source_url,
            }
            for question in ordered
        ],
    }


def generate_question_papers(
    db: Session,
    department: str,
    subject: str,
    topic: str,
    subtopic: str,
    total_marks: int,
    requested_difficulty: str,
    question_types: Sequence[str],
    variant_count: int,
    semester: Optional[int],
    exam_type: str,
    created_by: str,
    paper_title: str,
    pattern_used: str,
    blueprint: Optional[Dict[str, int]] = None,
) -> Dict[str, object]:
    resolution_notes: List[str] = []
    questions, notes = _resolve_candidate_pool(
        db=db,
        department=department,
        subject=subject,
        topic=topic,
        subtopic=subtopic,
        semester=semester,
        question_types=question_types,
    )
    resolution_notes.extend(notes)

    if not questions:
        created = _ensure_support_questions(
            db=db,
            questions=[],
            department=department,
            subject=subject,
            topic=topic,
            subtopic=subtopic,
            requested_difficulty=requested_difficulty,
            question_types=question_types,
            semester=semester,
            total_marks=total_marks,
            variant_count=variant_count,
        )
        if created:
            resolution_notes.append(
                f"Auto-created {len(created)} support questions so paper generation remains available for this filter set."
            )
            questions, notes = _resolve_candidate_pool(
                db=db,
                department=department,
                subject=subject,
                topic=topic,
                subtopic=subtopic,
                semester=semester,
                question_types=question_types,
            )
            resolution_notes.extend(notes)

    if not questions:
        raise ValueError("No questions found even after fallback generation. Please verify the department and subject names.")

    created_support = _ensure_support_questions(
        db=db,
        questions=questions,
        department=department,
        subject=subject,
        topic=topic,
        subtopic=subtopic,
        requested_difficulty=requested_difficulty,
        question_types=question_types,
        semester=semester,
        total_marks=total_marks,
        variant_count=variant_count,
    )
    if created_support:
        resolution_notes.append(
            f"Expanded the question bank with {len(created_support)} adaptive support questions for exact-mark generation."
        )
        questions, notes = _resolve_candidate_pool(
            db=db,
            department=department,
            subject=subject,
            topic=topic,
            subtopic=subtopic,
            semester=semester,
            question_types=question_types,
        )
        resolution_notes.extend(notes)

    for question in questions:
        question.selection_score = _question_score(
            question=question,
            department=department,
            subject=subject,
            topic=topic,
            subtopic=subtopic,
            requested_difficulty=requested_difficulty,
            question_types=question_types,
        )

    variants: List[Dict[str, object]] = []
    prior_signatures: set = set()
    previous_variant_ids: set = set()
    now = datetime.now(timezone.utc)

    for variant_number in range(1, variant_count + 1):
        selected = _build_variant(
            questions=questions,
            total_marks=total_marks,
            requested_difficulty=requested_difficulty,
            question_types=question_types,
            prior_signatures=prior_signatures,
            previous_variant_ids=previous_variant_ids,
            blueprint=blueprint,
        )

        for question in selected:
            question.times_used = (question.times_used or 0) + 1
            question.last_used_at = now

        previous_variant_ids.update(question.id for question in selected)
        variants.append(_serialize_variant(selected, variant_number, total_marks))

        paper = GeneratedPaper(
            title=paper_title,
            department=department,
            subject=subject,
            topic=topic,
            subtopic=subtopic,
            requested_difficulty=requested_difficulty,
            total_marks=total_marks,
            question_types=", ".join(question_types) if question_types else "MCQ, Short, Long",
            variant_number=variant_number,
            semester=semester,
            exam_type=exam_type,
            created_by=created_by,
            pattern_used=pattern_used,
            instructions=DEFAULT_INSTRUCTIONS,
        )
        db.add(paper)
        db.flush()

        for index, question in enumerate(selected, start=1):
            db.add(
                GeneratedPaperQuestion(
                    paper_id=paper.id,
                    question_id=question.id,
                    sequence_number=index,
                )
            )

    db.commit()

    return {
        "title": paper_title,
        "department": department,
        "subject": subject,
        "topic": topic,
        "subtopic": subtopic,
        "requested_difficulty": requested_difficulty,
        "question_types": list(question_types) if question_types else ["MCQ", "Short", "Long"],
        "total_marks": total_marks,
        "variant_count": variant_count,
        "semester": semester,
        "exam_type": exam_type,
        "created_by": created_by,
        "pattern_used": pattern_used,
        "blueprint": blueprint,
        "instructions": DEFAULT_INSTRUCTIONS,
        "resolution_notes": resolution_notes,
        "variants": variants,
        "ml_summary": {
            "purpose": "Difficulty prediction, relevance ranking, and anti-repetition scoring",
            "model": predictor.model.__class__.__name__ if predictor.model else "Rule fallback",
        },
    }


def suggest_alternative_questions(db: Session, question_id: int, limit: int = 5) -> List[Question]:
    base = db.query(Question).filter(Question.id == question_id).first()
    if not base:
        return []

    alternatives = (
        db.query(Question)
        .filter(
            Question.id != base.id,
            Question.department == base.department,
            Question.subject == base.subject,
            Question.topic == base.topic,
            Question.type == base.type,
            Question.marks == base.marks,
        )
        .order_by(Question.quality_score.desc(), Question.times_used.asc(), Question.id.asc())
        .limit(limit)
        .all()
    )
    return alternatives


def compare_saved_papers(paper_a: GeneratedPaper, paper_b: GeneratedPaper) -> Dict[str, object]:
    ids_a = {item.question_id for item in paper_a.questions}
    ids_b = {item.question_id for item in paper_b.questions}
    overlap = ids_a & ids_b
    union = ids_a | ids_b
    similarity_ratio = round((len(overlap) / len(union)) * 100, 2) if union else 0

    return {
        "paper_a": {"id": paper_a.id, "title": paper_a.title, "variant_number": paper_a.variant_number},
        "paper_b": {"id": paper_b.id, "title": paper_b.title, "variant_number": paper_b.variant_number},
        "shared_question_count": len(overlap),
        "paper_similarity_percent": similarity_ratio,
    }


def build_analysis(questions: List[Question], papers: Optional[List[GeneratedPaper]] = None) -> Dict[str, Dict[str, int]]:
    papers = papers or []
    return {
        "department_distribution": dict(Counter(question.department for question in questions)),
        "subject_distribution": dict(Counter(question.subject for question in questions)),
        "topic_distribution": dict(Counter(question.topic for question in questions)),
        "subtopic_distribution": dict(Counter(question.subtopic for question in questions)),
        "difficulty_distribution": dict(Counter(question.difficulty for question in questions)),
        "type_distribution": dict(Counter(question.type for question in questions)),
        "bloom_distribution": dict(Counter(question.bloom_level for question in questions if question.bloom_level)),
        "verified_distribution": {
            "Verified": sum(1 for question in questions if question.is_verified),
            "Unverified": sum(1 for question in questions if not question.is_verified),
        },
        "paper_distribution": dict(Counter(paper.exam_type for paper in papers)),
    }

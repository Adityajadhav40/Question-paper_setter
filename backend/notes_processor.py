import io
import re
from typing import List

from docx import Document
from pypdf import PdfReader


STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "about", "have", "has", "are",
    "was", "were", "their", "there", "which", "when", "where", "using", "used", "also", "than",
    "such", "these", "those", "through", "will", "shall", "can", "could", "would", "should",
}


def extract_text_from_upload(file_name: str, content: bytes) -> str:
    lower_name = file_name.lower()
    if lower_name.endswith(".pdf"):
        return extract_text_from_pdf(content)
    if lower_name.endswith(".docx"):
        return extract_text_from_docx(content)
    if lower_name.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")
    raise ValueError("Only PDF, DOCX, and TXT files are supported for note uploads.")


def extract_text_from_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_docx(content: bytes) -> str:
    document = Document(io.BytesIO(content))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def split_into_sentences(text: str) -> List[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    return [sentence.strip() for sentence in sentences if len(sentence.strip()) > 40]


def infer_keywords(text: str, limit: int = 10) -> List[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9\-]{3,}", text.lower())
    counts = {}
    for word in words:
        if word in STOPWORDS:
            continue
        counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [word.title() for word, _ in ranked[:limit]]


def generate_questions_from_notes(
    text: str,
    department: str,
    subject: str,
    topic: str,
    subtopic: str,
    max_questions: int = 15,
) -> List[dict]:
    sentences = split_into_sentences(text)
    keywords = infer_keywords(text)
    if not sentences:
        return []

    selected_sentences = sentences[:max_questions]
    generated: List[dict] = []
    keyword_fallback = keywords[0] if keywords else subtopic

    for index, sentence in enumerate(selected_sentences, start=1):
        if index % 3 == 1:
            question_type = "Short"
            difficulty = "Easy"
            marks = 2
            bloom_level = "Understand"
            question_text = f"Explain the following concept from the uploaded notes: {sentence}"
        elif index % 3 == 2:
            question_type = "Short"
            difficulty = "Medium"
            marks = 5
            bloom_level = "Apply"
            question_text = (
                f"Using the uploaded notes, discuss how {keyword_fallback} is connected to this idea: {sentence}"
            )
        else:
            question_type = "Long"
            difficulty = "Hard"
            marks = 10
            bloom_level = "Analyze"
            question_text = (
                f"Analyze and justify the following statement using the uploaded notes and examples: {sentence}"
            )

        generated.append(
            {
                "department": department,
                "subject": subject,
                "topic": topic,
                "subtopic": subtopic,
                "question": question_text,
                "answer": sentence,
                "difficulty": difficulty,
                "marks": marks,
                "type": question_type,
                "bloom_level": bloom_level,
                "semester": None,
                "course_outcome": "CO-Notes",
                "source_name": "Uploaded Notes",
                "source_url": None,
                "is_verified": False,
                "quality_score": 72,
            }
        )

    if keywords:
        generated.append(
            {
                "department": department,
                "subject": subject,
                "topic": topic,
                "subtopic": subtopic,
                "question": f"Which keyword best represents the main focus of the uploaded notes on {subtopic}?",
                "answer": ", ".join(keywords[:4]),
                "difficulty": "Easy",
                "marks": 2,
                "type": "MCQ",
                "bloom_level": "Remember",
                "semester": None,
                "course_outcome": "CO-Notes",
                "source_name": "Uploaded Notes",
                "source_url": None,
                "is_verified": False,
                "quality_score": 68,
            }
        )

    return generated[: max_questions + 1]

import json
import os
from typing import List

import requests


OPENAI_API_URL = "https://api.openai.com/v1/responses"


def is_openai_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def generate_questions_with_openai(
    notes_text: str,
    department: str,
    subject: str,
    topic: str,
    subtopic: str,
    max_questions: int = 10,
) -> List[dict]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    prompt = f"""
Generate a JSON array of at most {max_questions} engineering exam questions from the notes below.
Each item must include:
department, subject, topic, subtopic, question, answer, difficulty, marks, type, bloom_level, semester, course_outcome, source_name, source_url, is_verified, quality_score

Rules:
- department = {department}
- subject = {subject}
- topic = {topic}
- subtopic = {subtopic}
- type must be one of MCQ, Short, Long
- difficulty must be one of Easy, Medium, Hard
- marks should be 2, 5, or 10
- answer should be concise but useful
- semester can be null
- course_outcome can be CO-AI
- source_name must be OpenAI Notes Generation
- source_url must be null
- is_verified must be false
- quality_score should be between 70 and 85
- Return valid JSON only. No markdown.

Notes:
{notes_text[:12000]}
"""

    response = requests.post(
        OPENAI_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "input": prompt,
        },
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()

    text_chunks = []
    for output in payload.get("output", []):
        for content in output.get("content", []):
            if content.get("type") == "output_text":
                text_chunks.append(content.get("text", ""))

    raw_text = "\n".join(text_chunks).strip()
    if not raw_text:
        raise ValueError("OpenAI response did not contain question output.")

    return json.loads(raw_text)


def chat_with_openai(message: str, system_prompt: str = "") -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    prompt = f"{system_prompt}\n\nUser message:\n{message}".strip()

    response = requests.post(
        OPENAI_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "input": prompt,
        },
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()

    text_chunks = []
    for output in payload.get("output", []):
        for content in output.get("content", []):
            if content.get("type") == "output_text":
                text_chunks.append(content.get("text", ""))

    result = "\n".join(text_chunks).strip()
    if not result:
        raise ValueError("OpenAI response did not contain chat output.")
    return result

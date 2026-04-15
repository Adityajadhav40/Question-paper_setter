import csv
import io
import json
import logging
from pathlib import Path
from typing import Dict, List, Literal, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session, joinedload

from .ai_integration import chat_with_openai, generate_questions_with_openai, is_openai_configured
from .auth_utils import hash_password, verify_password
from .database import Base, SessionLocal, check_database_connection, engine, get_db
from .generator import build_analysis, compare_saved_papers, generate_question_papers, suggest_alternative_questions
from .ml_model import predictor
from .models import ExamBlueprint, FacultyUser, GeneratedPaper, GeneratedPaperQuestion, NoteDocument, Question
from .notes_processor import extract_text_from_upload, generate_questions_from_notes
from .seed_loader import load_seed_questions
from .similarity import find_similar_questions


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart AI Question Paper Generator", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


EXAM_TEMPLATES: Dict[str, dict] = {
    "Mid-Sem": {"marks": 40, "variants": 2, "pattern": "Balanced internal assessment"},
    "End-Sem": {"marks": 60, "variants": 3, "pattern": "University exam blueprint"},
    "Quiz": {"marks": 20, "variants": 1, "pattern": "Fast concept check"},
    "Lab Test": {"marks": 30, "variants": 2, "pattern": "Practical + explanation mix"},
    "Viva": {"marks": 25, "variants": 1, "pattern": "Oral and short reasoning prompts"},
}


class QuestionCreate(BaseModel):
    department: str = Field(..., min_length=2)
    subject: str = Field(..., min_length=2)
    topic: str = Field(..., min_length=2)
    subtopic: str = Field(..., min_length=2)
    question: str = Field(..., min_length=5)
    answer: Optional[str] = None
    difficulty: Literal["Easy", "Medium", "Hard"]
    marks: int = Field(..., gt=0, le=50)
    type: Literal["MCQ", "Short", "Long"]
    bloom_level: Optional[Literal["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]] = None
    semester: Optional[int] = Field(default=None, ge=1, le=8)
    course_outcome: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    is_verified: bool = False
    approval_status: Literal["draft", "approved", "rejected"] = "draft"
    review_notes: Optional[str] = None
    quality_score: int = Field(default=75, ge=1, le=100)


class BulkImportRequest(BaseModel):
    questions: List[QuestionCreate] = Field(default_factory=list, min_length=1)


class GeneratePaperRequest(BaseModel):
    department: str = Field(..., min_length=2)
    subject: str = Field(..., min_length=2)
    topic: str = "All Topics"
    subtopic: str = "All Subtopics"
    difficulty: Literal["Mixed", "Easy", "Medium", "Hard"] = "Mixed"
    total_marks: int = Field(..., gt=0, le=100)
    question_types: List[Literal["MCQ", "Short", "Long"]] = Field(default_factory=list)
    variant_count: int = Field(default=3, ge=1, le=5)
    semester: Optional[int] = Field(default=None, ge=1, le=8)
    exam_type: Literal["Mid-Sem", "End-Sem", "Quiz", "Lab Test", "Viva", "Custom"] = "Custom"
    created_by: str = "Faculty User"
    paper_title: str = "Smart Question Paper"
    pattern_used: str = "AI balanced selection"
    blueprint: Optional[Dict[str, int]] = None


class FacultyRegisterRequest(BaseModel):
    full_name: str
    username: str
    password: str
    role: Literal["faculty", "admin"] = "faculty"
    department: Optional[str] = None


class FacultyLoginRequest(BaseModel):
    username: str
    password: str


class BlueprintCreateRequest(BaseModel):
    name: str
    exam_type: str
    blueprint: Dict[str, int]
    created_by: str


class ReviewQuestionRequest(BaseModel):
    approval_status: Literal["approved", "rejected", "draft"]
    review_notes: Optional[str] = None
    quality_score: int = Field(default=80, ge=1, le=100)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


def migrate_existing_schema() -> None:
    inspector = inspect(engine)
    if "questions" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("questions")}
    with engine.begin() as connection:
        upgrades = {
            "department": "ALTER TABLE questions ADD COLUMN department VARCHAR(120)",
            "subject": "ALTER TABLE questions ADD COLUMN subject VARCHAR(120)",
            "topic": None,
            "subtopic": "ALTER TABLE questions ADD COLUMN subtopic VARCHAR(120)",
            "answer": "ALTER TABLE questions ADD COLUMN answer TEXT",
            "bloom_level": "ALTER TABLE questions ADD COLUMN bloom_level VARCHAR(40)",
            "semester": "ALTER TABLE questions ADD COLUMN semester INTEGER",
            "course_outcome": "ALTER TABLE questions ADD COLUMN course_outcome VARCHAR(60)",
            "source_name": "ALTER TABLE questions ADD COLUMN source_name VARCHAR(200)",
            "source_url": "ALTER TABLE questions ADD COLUMN source_url VARCHAR(500)",
            "is_verified": "ALTER TABLE questions ADD COLUMN is_verified BOOLEAN DEFAULT FALSE",
            "approval_status": "ALTER TABLE questions ADD COLUMN approval_status VARCHAR(20) DEFAULT 'draft'",
            "review_notes": "ALTER TABLE questions ADD COLUMN review_notes TEXT",
            "quality_score": "ALTER TABLE questions ADD COLUMN quality_score INTEGER DEFAULT 70",
            "times_used": "ALTER TABLE questions ADD COLUMN times_used INTEGER DEFAULT 0",
            "last_used_at": "ALTER TABLE questions ADD COLUMN last_used_at TIMESTAMPTZ",
            "created_at": "ALTER TABLE questions ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW()",
            "updated_at": "ALTER TABLE questions ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW()",
        }
        for column, statement in upgrades.items():
            if column not in columns and statement:
                connection.execute(text(statement))

        connection.execute(
            text(
                """
                UPDATE questions
                SET department = COALESCE(department, 'General Engineering'),
                    subject = COALESCE(subject, topic),
                    subtopic = COALESCE(subtopic, topic),
                    answer = COALESCE(answer, 'Answer key to be added.'),
                    bloom_level = COALESCE(bloom_level, 'Understand'),
                    semester = COALESCE(semester, 3),
                    course_outcome = COALESCE(course_outcome, 'CO-1'),
                    source_name = COALESCE(source_name, 'Legacy Import'),
                    approval_status = COALESCE(approval_status, 'draft'),
                    quality_score = COALESCE(quality_score, 70),
                    times_used = COALESCE(times_used, 0),
                    is_verified = COALESCE(is_verified, FALSE)
                """
            )
        )

    inspector = inspect(engine)
    if "generated_papers" in inspector.get_table_names():
        paper_columns = {column["name"] for column in inspector.get_columns("generated_papers")}
        with engine.begin() as connection:
            paper_upgrades = {
                "title": "ALTER TABLE generated_papers ADD COLUMN title VARCHAR(200)",
                "subtopic": "ALTER TABLE generated_papers ADD COLUMN subtopic VARCHAR(120) DEFAULT 'All Subtopics'",
                "semester": "ALTER TABLE generated_papers ADD COLUMN semester INTEGER",
                "exam_type": "ALTER TABLE generated_papers ADD COLUMN exam_type VARCHAR(50) DEFAULT 'Custom'",
                "created_by": "ALTER TABLE generated_papers ADD COLUMN created_by VARCHAR(120) DEFAULT 'Faculty User'",
                "pattern_used": "ALTER TABLE generated_papers ADD COLUMN pattern_used VARCHAR(200) DEFAULT 'AI balanced selection'",
                "instructions": "ALTER TABLE generated_papers ADD COLUMN instructions TEXT",
            }
            for column, statement in paper_upgrades.items():
                if column not in paper_columns:
                    connection.execute(text(statement))
            connection.execute(
                text(
                    """
                    UPDATE generated_papers
                    SET title = COALESCE(title, subject || ' Question Paper'),
                        subtopic = COALESCE(subtopic, 'All Subtopics'),
                        exam_type = COALESCE(exam_type, 'Custom'),
                        created_by = COALESCE(created_by, 'Faculty User'),
                        pattern_used = COALESCE(pattern_used, 'AI balanced selection')
                    """
                )
            )

    Base.metadata.create_all(bind=engine)


def seed_sample_data() -> None:
    db = SessionLocal()
    try:
        seed_questions = load_seed_questions()
        existing = {row[0] for row in db.query(Question.question).all()}
        inserted = 0
        for row in seed_questions:
            if row["question"] in existing:
                continue
            db.add(Question(**row))
            inserted += 1
        db.commit()
        logger.info("Inserted %s seed questions from dataset file.", inserted)
    except Exception:
        db.rollback()
        logger.exception("Failed to seed sample data.")
        raise
    finally:
        db.close()


def seed_defaults() -> None:
    db = SessionLocal()
    try:
        if not db.query(FacultyUser).filter(FacultyUser.username == "admin").first():
            db.add(
                FacultyUser(
                    full_name="System Admin",
                    username="admin",
                    password_hash=hash_password("admin123"),
                    role="admin",
                    department="All Departments",
                )
            )

        for name, config in EXAM_TEMPLATES.items():
            if not db.query(ExamBlueprint).filter(ExamBlueprint.name == name).first():
                default_blueprint = {"MCQ": max(0, int(config["marks"] * 0.2)), "Short": max(0, int(config["marks"] * 0.3))}
                remaining = config["marks"] - sum(default_blueprint.values())
                default_blueprint["Long"] = max(0, remaining)
                db.add(
                    ExamBlueprint(
                        name=name,
                        exam_type=name,
                        blueprint_json=json.dumps(default_blueprint),
                        created_by="System Admin",
                    )
                )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to seed default users/blueprints.")
        raise
    finally:
        db.close()


def train_model_from_database() -> None:
    db = SessionLocal()
    try:
        predictor.train(db.query(Question).all())
    finally:
        db.close()


@app.on_event("startup")
def startup_event() -> None:
    check_database_connection()
    Base.metadata.create_all(bind=engine)
    migrate_existing_schema()
    Base.metadata.create_all(bind=engine)
    seed_sample_data()
    seed_defaults()
    train_model_from_database()
    logger.info("Application startup completed.")


def serialize_question(question: Question) -> dict:
    return {
        "id": question.id,
        "department": question.department,
        "subject": question.subject,
        "topic": question.topic,
        "subtopic": question.subtopic,
        "question": question.question,
        "answer": question.answer,
        "difficulty": question.difficulty,
        "marks": question.marks,
        "type": question.type,
        "bloom_level": question.bloom_level,
        "semester": question.semester,
        "course_outcome": question.course_outcome,
        "source_name": question.source_name,
        "source_url": question.source_url,
        "is_verified": question.is_verified,
        "approval_status": question.approval_status,
        "review_notes": question.review_notes,
        "quality_score": question.quality_score,
        "times_used": question.times_used,
    }


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/filters")
def get_filters(db: Session = Depends(get_db)):
    questions = db.query(Question).order_by(Question.department, Question.subject, Question.topic, Question.subtopic).all()
    hierarchy: Dict[str, Dict[str, Dict[str, List[str]]]] = {}
    for question in questions:
        subject_bucket = hierarchy.setdefault(question.department, {}).setdefault(question.subject, {})
        subtopics = subject_bucket.setdefault(question.topic, [])
        if question.subtopic not in subtopics:
            subtopics.append(question.subtopic)

    for department in hierarchy.values():
        for subject in department.values():
            for subtopics in subject.values():
                subtopics.sort()

    return {
        "departments": hierarchy,
        "question_types": ["MCQ", "Short", "Long"],
        "difficulties": ["Mixed", "Easy", "Medium", "Hard"],
        "bloom_levels": ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"],
        "semesters": [1, 2, 3, 4, 5, 6, 7, 8],
        "exam_templates": EXAM_TEMPLATES,
    }


@app.get("/dashboard-summary")
def dashboard_summary(db: Session = Depends(get_db)):
    question_count = db.query(Question).count()
    paper_count = db.query(GeneratedPaper).count()
    departments = db.query(Question.department).distinct().count()
    subjects = db.query(Question.subject).distinct().count()
    verified = db.query(Question).filter(Question.is_verified.is_(True)).count()
    return {
        "question_count": question_count,
        "paper_count": paper_count,
        "department_count": departments,
        "subject_count": subjects,
        "verified_count": verified,
        "unverified_count": max(0, question_count - verified),
    }


@app.post("/auth/register")
def register_faculty(payload: FacultyRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(FacultyUser).filter(FacultyUser.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists.")

    user = FacultyUser(
        full_name=payload.full_name,
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        department=payload.department,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Faculty user created successfully.", "user": {"username": user.username, "role": user.role}}


@app.post("/auth/login")
def login_faculty(payload: FacultyLoginRequest, db: Session = Depends(get_db)):
    user = db.query(FacultyUser).filter(FacultyUser.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {
        "message": "Login successful.",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "username": user.username,
            "role": user.role,
            "department": user.department,
        },
    }


@app.get("/blueprints")
def get_blueprints(db: Session = Depends(get_db)):
    rows = db.query(ExamBlueprint).order_by(ExamBlueprint.name.asc()).all()
    return {
        "count": len(rows),
        "blueprints": [
            {
                "id": row.id,
                "name": row.name,
                "exam_type": row.exam_type,
                "blueprint": json.loads(row.blueprint_json),
                "created_by": row.created_by,
            }
            for row in rows
        ],
    }


@app.post("/blueprints")
def create_blueprint(payload: BlueprintCreateRequest, db: Session = Depends(get_db)):
    row = ExamBlueprint(
        name=payload.name,
        exam_type=payload.exam_type,
        blueprint_json=json.dumps(payload.blueprint),
        created_by=payload.created_by,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"message": "Blueprint created successfully.", "id": row.id}


@app.get("/questions")
def get_questions(limit: int = 200, db: Session = Depends(get_db)):
    questions = (
        db.query(Question)
        .order_by(Question.department, Question.subject, Question.topic, Question.subtopic, Question.id)
        .limit(limit)
        .all()
    )
    return {"count": len(questions), "questions": [serialize_question(question) for question in questions]}


@app.post("/add-question")
def add_question(payload: QuestionCreate, db: Session = Depends(get_db)):
    try:
        question = Question(**payload.model_dump())
        db.add(question)
        db.commit()
        db.refresh(question)
        train_model_from_database()
        return {"message": "Question added successfully.", "question": serialize_question(question)}
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to add question.")
        raise HTTPException(status_code=500, detail=f"Unable to add question: {exc}") from exc


@app.post("/import-questions")
def import_questions(payload: BulkImportRequest, db: Session = Depends(get_db)):
    try:
        existing = {row[0] for row in db.query(Question.question).all()}
        inserted = 0
        skipped = 0
        for item in payload.questions:
            row = item.model_dump()
            if row["question"] in existing:
                skipped += 1
                continue
            db.add(Question(**row))
            inserted += 1
        db.commit()
        train_model_from_database()
        return {"message": "Bulk import completed.", "inserted": inserted, "skipped": skipped}
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to import questions.")
        raise HTTPException(status_code=500, detail=f"Unable to import questions: {exc}") from exc


@app.post("/import-file")
async def import_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()
        name = (file.filename or "").lower()
        rows: List[dict]

        if name.endswith(".json"):
            payload = json.loads(content.decode("utf-8"))
            rows = payload.get("questions", payload) if isinstance(payload, dict) else payload
        elif name.endswith(".csv"):
            text_content = content.decode("utf-8-sig")
            rows = list(csv.DictReader(io.StringIO(text_content)))
        else:
            raise HTTPException(status_code=400, detail="Only JSON and CSV files are supported.")

        normalized = [QuestionCreate(**row).model_dump() for row in rows]
        existing = {row[0] for row in db.query(Question.question).all()}
        inserted = 0
        skipped = 0
        for row in normalized:
            if row["question"] in existing:
                skipped += 1
                continue
            db.add(Question(**row))
            inserted += 1

        db.commit()
        train_model_from_database()
        return {"message": "File import completed.", "inserted": inserted, "skipped": skipped}
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to import uploaded file.")
        raise HTTPException(status_code=500, detail=f"Unable to import file: {exc}") from exc


@app.post("/upload-notes")
async def upload_notes(
    file: UploadFile = File(...),
    department: str = Form(...),
    subject: str = Form(...),
    topic: str = Form(...),
    subtopic: str = Form(...),
    title: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        content = await file.read()
        extracted_text = extract_text_from_upload(file.filename or "uploaded-file", content)
        if len(extracted_text.strip()) < 120:
            raise HTTPException(status_code=400, detail="Uploaded notes do not contain enough readable text.")

        generated_questions = generate_questions_from_notes(
            text=extracted_text,
            department=department,
            subject=subject,
            topic=topic,
            subtopic=subtopic,
        )
        if not generated_questions:
            raise HTTPException(status_code=400, detail="Could not generate questions from the uploaded notes.")

        note_document = NoteDocument(
            title=title,
            department=department,
            subject=subject,
            topic=topic,
            subtopic=subtopic,
            file_name=file.filename or "uploaded-file",
            file_type=Path(file.filename or "uploaded-file").suffix.lower().replace(".", "") or "unknown",
            extracted_text=extracted_text[:50000],
            generated_question_count=len(generated_questions),
        )
        db.add(note_document)
        db.flush()

        existing = {row[0] for row in db.query(Question.question).all()}
        inserted = 0
        preview = []
        for row in generated_questions:
            if row["question"] in existing:
                continue
            question = Question(**row)
            db.add(question)
            inserted += 1
            if len(preview) < 6:
                preview.append(row)

        db.commit()
        train_model_from_database()
        return {
            "message": "Notes uploaded and converted into questions successfully.",
            "note_title": title,
            "inserted_questions": inserted,
            "preview_questions": preview,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to process uploaded notes.")
        raise HTTPException(status_code=500, detail=f"Unable to process uploaded notes: {exc}") from exc


@app.post("/upload-notes-ai")
async def upload_notes_ai(
    file: UploadFile = File(...),
    department: str = Form(...),
    subject: str = Form(...),
    topic: str = Form(...),
    subtopic: str = Form(...),
    title: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        content = await file.read()
        extracted_text = extract_text_from_upload(file.filename or "uploaded-file", content)
        used_fallback = False
        if is_openai_configured():
            try:
                generated_questions = generate_questions_with_openai(
                    notes_text=extracted_text,
                    department=department,
                    subject=subject,
                    topic=topic,
                    subtopic=subtopic,
                )
            except Exception:
                logger.exception("AI note generation failed; falling back to local note processor.")
                generated_questions = generate_questions_from_notes(
                    text=extracted_text,
                    department=department,
                    subject=subject,
                    topic=topic,
                    subtopic=subtopic,
                )
                used_fallback = True
        else:
            generated_questions = generate_questions_from_notes(
                text=extracted_text,
                department=department,
                subject=subject,
                topic=topic,
                subtopic=subtopic,
            )
            used_fallback = True

        note_document = NoteDocument(
            title=title,
            department=department,
            subject=subject,
            topic=topic,
            subtopic=subtopic,
            file_name=file.filename or "uploaded-file",
            file_type=Path(file.filename or "uploaded-file").suffix.lower().replace(".", "") or "unknown",
            extracted_text=extracted_text[:50000],
            generated_question_count=len(generated_questions),
        )
        db.add(note_document)
        existing = {row[0] for row in db.query(Question.question).all()}
        inserted = 0
        for row in generated_questions:
            normalized = QuestionCreate(**row).model_dump()
            if normalized["question"] in existing:
                continue
            db.add(Question(**normalized))
            inserted += 1
        db.commit()
        train_model_from_database()
        return {
            "message": "AI note generation completed." if not used_fallback else "AI was unavailable, so local note generation was used.",
            "inserted_questions": inserted,
            "used_fallback": used_fallback,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to generate questions with AI.")
        raise HTTPException(status_code=500, detail=f"Unable to process AI note generation: {exc}") from exc


@app.get("/review-queue")
def review_queue(limit: int = 50, db: Session = Depends(get_db)):
    questions = (
        db.query(Question)
        .filter((Question.approval_status != "approved") | (Question.is_verified.is_(False)))
        .order_by(Question.quality_score.asc(), Question.id.desc())
        .limit(limit)
        .all()
    )
    return {"count": len(questions), "questions": [serialize_question(question) for question in questions]}


@app.post("/questions/{question_id}/review")
def review_question(question_id: int, payload: ReviewQuestionRequest, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")
    question.approval_status = payload.approval_status
    question.review_notes = payload.review_notes
    question.quality_score = payload.quality_score
    question.is_verified = payload.approval_status == "approved"
    db.commit()
    db.refresh(question)
    return {"message": "Question review updated.", "question": serialize_question(question)}


@app.get("/question-quality-review")
def question_quality_review(limit: int = 50, db: Session = Depends(get_db)):
    low_quality = (
        db.query(Question)
        .filter((Question.quality_score < 75) | (Question.times_used > 4) | (Question.is_verified.is_(False)))
        .order_by(Question.quality_score.asc(), Question.times_used.desc())
        .limit(limit)
        .all()
    )
    return {"count": len(low_quality), "questions": [serialize_question(question) for question in low_quality]}


@app.get("/questions/{question_id}/similar")
def question_similarity(question_id: int, threshold: float = 0.72, db: Session = Depends(get_db)):
    base = db.query(Question).filter(Question.id == question_id).first()
    if not base:
        raise HTTPException(status_code=404, detail="Question not found.")
    candidates = db.query(Question).filter(Question.subject == base.subject).all()
    similar = find_similar_questions(base, candidates, threshold=threshold)
    return {
        "question": serialize_question(base),
        "matches": [
            {"question": serialize_question(question), "similarity": round(score, 3)}
            for question, score in similar[:20]
        ],
    }


@app.get("/questions/{question_id}/alternatives")
def question_alternatives(question_id: int, db: Session = Depends(get_db)):
    alternatives = suggest_alternative_questions(db, question_id)
    return {"count": len(alternatives), "alternatives": [serialize_question(question) for question in alternatives]}


@app.post("/generate-paper")
def generate_paper(payload: GeneratePaperRequest, db: Session = Depends(get_db)):
    try:
        bundle = generate_question_papers(
            db=db,
            department=payload.department,
            subject=payload.subject,
            topic=payload.topic,
            subtopic=payload.subtopic,
            total_marks=payload.total_marks,
            requested_difficulty=payload.difficulty,
            question_types=payload.question_types,
            variant_count=payload.variant_count,
            semester=payload.semester,
            exam_type=payload.exam_type,
            created_by=payload.created_by,
            paper_title=payload.paper_title,
            pattern_used=payload.pattern_used,
            blueprint=payload.blueprint,
        )
        return {"message": "Question paper variants generated successfully.", "paper_bundle": bundle}
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to generate paper.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@app.get("/analysis")
def analysis(db: Session = Depends(get_db)):
    questions = db.query(Question).all()
    papers = db.query(GeneratedPaper).all()
    return build_analysis(questions, papers)


@app.get("/generated-papers")
def generated_papers(limit: int = 20, db: Session = Depends(get_db)):
    papers = (
        db.query(GeneratedPaper)
        .options(joinedload(GeneratedPaper.questions).joinedload(GeneratedPaperQuestion.question))
        .order_by(GeneratedPaper.created_at.desc(), GeneratedPaper.id.desc())
        .limit(limit)
        .all()
    )
    return {
        "count": len(papers),
        "papers": [
            {
                "id": paper.id,
                "title": paper.title,
                "department": paper.department,
                "subject": paper.subject,
                "topic": paper.topic,
                "subtopic": paper.subtopic,
                "requested_difficulty": paper.requested_difficulty,
                "total_marks": paper.total_marks,
                "question_types": paper.question_types,
                "variant_number": paper.variant_number,
                "semester": paper.semester,
                "exam_type": paper.exam_type,
                "created_by": paper.created_by,
                "pattern_used": paper.pattern_used,
                "created_at": paper.created_at.isoformat() if paper.created_at else None,
                "questions": [
                    {
                        "sequence_number": item.sequence_number,
                        "question": item.question.question,
                        "answer": item.question.answer,
                        "marks": item.question.marks,
                        "type": item.question.type,
                        "difficulty": item.question.difficulty,
                    }
                    for item in sorted(paper.questions, key=lambda row: row.sequence_number)
                ],
            }
            for paper in papers
        ],
    }


@app.get("/notes-library")
def notes_library(limit: int = 20, db: Session = Depends(get_db)):
    notes = (
        db.query(NoteDocument)
        .order_by(NoteDocument.created_at.desc(), NoteDocument.id.desc())
        .limit(limit)
        .all()
    )
    return {
        "count": len(notes),
        "notes": [
            {
                "id": note.id,
                "title": note.title,
                "department": note.department,
                "subject": note.subject,
                "topic": note.topic,
                "subtopic": note.subtopic,
                "file_name": note.file_name,
                "file_type": note.file_type,
                "generated_question_count": note.generated_question_count,
                "created_at": note.created_at.isoformat() if note.created_at else None,
            }
            for note in notes
        ],
    }


@app.get("/compare-papers")
def compare_papers(paper_a_id: int, paper_b_id: int, db: Session = Depends(get_db)):
    paper_a = (
        db.query(GeneratedPaper)
        .options(joinedload(GeneratedPaper.questions))
        .filter(GeneratedPaper.id == paper_a_id)
        .first()
    )
    paper_b = (
        db.query(GeneratedPaper)
        .options(joinedload(GeneratedPaper.questions))
        .filter(GeneratedPaper.id == paper_b_id)
        .first()
    )
    if not paper_a or not paper_b:
        raise HTTPException(status_code=404, detail="One or both papers were not found.")
    return compare_saved_papers(paper_a, paper_b)


@app.get("/ml-info")
def ml_info():
    return {
        "enabled": predictor.model is not None,
        "openai_notes_enabled": is_openai_configured(),
        "openai_chat_enabled": is_openai_configured(),
        "usage": [
            "Predicts likely difficulty based on academic metadata and question style",
            "Ranks questions by relevance, quality, freshness, and past usage",
            "Helps diversify variants and reduce repetition across generated papers",
        ],
        "api_usage": [
            "The frontend dashboard uses fetch() to load filters, analytics, imports, and generated papers",
            "The backend exposes REST APIs for question bank management and paper generation",
        ],
    }


@app.post("/chat")
def chat(payload: ChatRequest):
    try:
        if is_openai_configured():
            try:
                reply = chat_with_openai(
                    payload.message,
                    system_prompt=(
                        "You are a helpful academic project assistant inside the Smart AI Question Paper Generator. "
                        "Answer clearly and conversationally. You can help with study questions, project usage, "
                        "engineering topics, and general productivity."
                    ),
                )
            except Exception:
                logger.exception("OpenAI chat failed; returning local fallback response.")
                reply = (
                    "OpenAI chat is temporarily unavailable or rate-limited. Local fallback mode is active. "
                    "You can still use Generate for papers, Manage for imports and notes, and Intelligence for "
                    "blueprint, review, similarity, and comparison tools."
                )
        else:
            reply = (
                "AI chat is available after setting OPENAI_API_KEY. For now, I can still help with the project: "
                "use Generate for papers, Manage for imports and notes, and Intelligence for blueprint, review, "
                "similarity, and comparison tools."
            )
        return {"reply": reply, "openai_enabled": is_openai_configured()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat failed: {exc}") from exc


@app.get("/source-library")
def source_library():
    return {
        "dataset_file": str((BASE_DIR / "data" / "questions_seed.json").name),
        "recommended_sources": [
            {
                "name": "MIT OpenCourseWare",
                "type": "Open exams, assignments, and problem sets",
                "url": "https://ocw.mit.edu/",
            },
            {
                "name": "NPTEL Official Courses",
                "type": "Engineering course materials and assessments",
                "url": "https://onlinecourses.nptel.ac.in/",
            },
            {
                "name": "SWAYAM",
                "type": "Official MOOC platform with engineering courses",
                "url": "https://swayam.gov.in/",
            },
        ],
        "import_options": ["POST /import-questions", "POST /import-file", "POST /upload-notes", "POST /upload-notes-ai"],
        "note": "Prefer curated and openly available academic content. Review imported data before marking it verified.",
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Smart AI Question Paper Generator"}


app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

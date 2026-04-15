from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    department = Column(String(120), nullable=False, index=True)
    subject = Column(String(120), nullable=False, index=True)
    topic = Column(String(120), nullable=False, index=True)
    subtopic = Column(String(120), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    difficulty = Column(String(20), nullable=False, index=True)
    marks = Column(Integer, nullable=False)
    type = Column(String(20), nullable=False, index=True)
    bloom_level = Column(String(40), nullable=True, index=True)
    semester = Column(Integer, nullable=True, index=True)
    course_outcome = Column(String(60), nullable=True)
    source_name = Column(String(200), nullable=True)
    source_url = Column(String(500), nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False, server_default="false")
    approval_status = Column(String(20), nullable=False, default="draft", server_default="draft")
    review_notes = Column(Text, nullable=True)
    quality_score = Column(Integer, nullable=False, default=70, server_default="70")
    times_used = Column(Integer, nullable=False, default=0, server_default="0")
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    generated_links = relationship("GeneratedPaperQuestion", back_populates="question")


class GeneratedPaper(Base):
    __tablename__ = "generated_papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    department = Column(String(120), nullable=False, index=True)
    subject = Column(String(120), nullable=False, index=True)
    topic = Column(String(120), nullable=False)
    subtopic = Column(String(120), nullable=False)
    requested_difficulty = Column(String(20), nullable=False)
    total_marks = Column(Integer, nullable=False)
    question_types = Column(String(200), nullable=False)
    variant_number = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=True)
    exam_type = Column(String(50), nullable=False)
    created_by = Column(String(120), nullable=False)
    pattern_used = Column(String(200), nullable=False)
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    questions = relationship(
        "GeneratedPaperQuestion",
        back_populates="paper",
        cascade="all, delete-orphan",
    )


class GeneratedPaperQuestion(Base):
    __tablename__ = "generated_paper_questions"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("generated_papers.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)

    paper = relationship("GeneratedPaper", back_populates="questions")
    question = relationship("Question", back_populates="generated_links")


class NoteDocument(Base):
    __tablename__ = "note_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    department = Column(String(120), nullable=False, index=True)
    subject = Column(String(120), nullable=False, index=True)
    topic = Column(String(120), nullable=False, index=True)
    subtopic = Column(String(120), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    extracted_text = Column(Text, nullable=False)
    generated_question_count = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FacultyUser(Base):
    __tablename__ = "faculty_users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    username = Column(String(80), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="faculty", server_default="faculty")
    department = Column(String(120), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ExamBlueprint(Base):
    __tablename__ = "exam_blueprints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True)
    exam_type = Column(String(50), nullable=False)
    blueprint_json = Column(Text, nullable=False)
    created_by = Column(String(120), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

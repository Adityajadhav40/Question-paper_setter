# Smart AI Question Paper Generator
## Project Report for Deep Learning and AI/ML Subject

## 1. Title
Smart AI Question Paper Generator with ML-Assisted Question Selection, Notes-to-Question Generation, Analytics, Review Workflow, and Optional OpenAI Integration

## 2. Abstract
This project is a full-stack academic automation system developed to generate smart question papers from a structured question bank. The system is designed for engineering departments and supports department-wise, subject-wise, topic-wise, and subtopic-wise filtering. It stores the question bank in a relational database, generates balanced papers according to difficulty and type distribution, saves generated variants, provides analytics, supports review and approval workflow, allows question import from JSON/CSV, and can generate draft questions from uploaded notes. The project uses FastAPI as the backend framework, PostgreSQL as the main database target, SQLAlchemy ORM for database interaction, and Scikit-learn Random Forest for machine-learning-based difficulty prediction and ranking support. Optional OpenAI integration is also included for AI-assisted note-to-question generation and chat support.

## 3. Problem Statement
Traditional question paper preparation is time-consuming, repetitive, and difficult to scale across departments and subjects. Faculty members often need to:
- search questions manually from notes, previous papers, and question banks
- balance paper difficulty and question types
- avoid repeated questions
- generate multiple paper variants
- store answer keys and topic mappings
- review question quality and approval status

This project solves these issues by automating question organization, filtering, ranking, generation, storage, and analytics.

## 4. Objectives
- Build an AI/ML-enabled question paper generation system
- Store and manage a structured engineering question bank
- Generate balanced exam papers automatically
- Support multiple paper variants
- Predict difficulty using machine learning
- Generate questions from uploaded notes
- Add review, approval, similarity detection, and analytics
- Provide a modern frontend dashboard for faculty/admin use

## 5. Subject Relevance: Deep Learning and AI/ML
This project is strongly aligned with AI/ML because it applies:
- machine learning for difficulty prediction
- feature engineering for educational metadata
- heuristic intelligence for balanced paper generation
- note-processing for automated question extraction
- similarity analysis for duplicate detection
- optional LLM integration for advanced AI question generation and AI chat

Important academic note:
The current production model in this project is a classical ML model, not a deep neural network. Specifically, the system uses `RandomForestClassifier` from Scikit-learn. For a Deep Learning subject, this is still valid because:
- it is an AI/ML project with clear applied intelligence
- it can be extended to deep learning for NLP, embeddings, semantic similarity, and automatic question generation
- the current architecture is ready for such upgrades

## 6. Technology Stack
### Backend
- Python
- FastAPI
- Uvicorn

### Database
- PostgreSQL as the intended primary database
- SQLAlchemy ORM for model mapping and queries

### ML / AI
- Scikit-learn
- RandomForestClassifier
- feature encoding with OneHotEncoder
- preprocessing with ColumnTransformer
- optional OpenAI Responses API integration

### Frontend
- HTML
- CSS
- JavaScript
- Chart-based data visualization

### Utilities
- pypdf for PDF text extraction
- python-docx for DOCX note extraction
- requests for OpenAI API calls

## 7. Main Modules in the Project
### 7.1 Database Module
File: `backend/database.py`

Purpose:
- creates database engine
- initializes SQLAlchemy session
- handles DB connection lifecycle

### 7.2 Data Models
File: `backend/models.py`

Purpose:
- defines tables such as:
  - `questions`
  - `generated_papers`
  - `generated_paper_questions`
  - `note_documents`
  - `faculty_users`
  - `exam_blueprints`

### 7.3 ML Module
File: `backend/ml_model.py`

Purpose:
- trains the ML model on question metadata
- predicts likely question difficulty

### 7.4 Generator Engine
File: `backend/generator.py`

Purpose:
- filters questions
- computes type and difficulty distribution
- searches exact mark combinations
- ranks candidate questions
- generates paper variants
- stores generated papers

### 7.5 Notes Processing
File: `backend/notes_processor.py`

Purpose:
- extracts text from PDF, DOCX, and TXT notes
- generates draft questions from note content

### 7.6 Optional LLM Integration
File: `backend/ai_integration.py`

Purpose:
- uses OpenAI API for:
  - question generation from uploaded notes
  - AI chat assistant

### 7.7 Similarity Module
File: `backend/similarity.py`

Purpose:
- compares question text using similarity ratio
- identifies near-duplicate questions

### 7.8 API Layer
File: `backend/main.py`

Purpose:
- startup and migration
- seeding
- REST API routes
- auth endpoints
- generation endpoints
- analysis endpoints

## 8. Database Design
### 8.1 questions table
Used to store the main question bank.

Main fields:
- `id`
- `department`
- `subject`
- `topic`
- `subtopic`
- `question`
- `answer`
- `difficulty`
- `marks`
- `type`
- `bloom_level`
- `semester`
- `course_outcome`
- `source_name`
- `source_url`
- `is_verified`
- `approval_status`
- `review_notes`
- `quality_score`
- `times_used`
- `last_used_at`

### 8.2 generated_papers table
Stores generated paper metadata.

Fields:
- `title`
- `department`
- `subject`
- `topic`
- `subtopic`
- `requested_difficulty`
- `total_marks`
- `question_types`
- `variant_number`
- `semester`
- `exam_type`
- `created_by`
- `pattern_used`
- `instructions`

### 8.3 generated_paper_questions table
Stores mapping between generated papers and selected questions.

### 8.4 note_documents table
Stores uploaded note metadata and extracted text summary.

### 8.5 faculty_users table
Stores demo faculty/admin users.

### 8.6 exam_blueprints table
Stores reusable paper generation patterns.

## 9. Algorithms and Intelligence Used
### 9.1 Random Forest Classifier
Used in: `backend/ml_model.py`

Why used:
- robust classical ML model
- handles structured categorical + numerical features well
- simple to train and explain
- good for educational metadata classification

Input features:
- department
- subject
- topic
- subtopic
- marks
- type
- semester
- bloom_level
- times_used

Target:
- `difficulty`

Use in project:
- after training, the model predicts the likely difficulty of each question
- this prediction supports the ranking function used by the generator
- it improves selection quality when creating papers

### 9.2 Heuristic Scoring Algorithm
Used in: `backend/generator.py`

The generator computes a custom score based on:
- department match
- subject match
- topic match
- subtopic match
- requested difficulty
- predicted difficulty
- question type
- quality score
- verification status
- times used

Purpose:
- pick better questions, not just random ones
- avoid overused questions
- prefer relevant and higher-quality questions

### 9.3 Exact Marks Combination Search
Used in: `backend/generator.py`

Technique:
- recursive backtracking / subset search

Purpose:
- select question combinations whose marks exactly equal the required total

Why important:
- exam papers must match total marks exactly

### 9.4 Difficulty Distribution Logic
Used in mixed-paper generation:
- 30% Easy
- 50% Medium
- 20% Hard

This helps create balanced papers.

### 9.5 Type Distribution / Blueprint Logic
Question type target logic supports:
- MCQ
- Short
- Long

Blueprints can define exact mark allocation by question type.

### 9.6 Similarity Detection
Used in: `backend/similarity.py`

Technique:
- text similarity ratio using sequence comparison

Purpose:
- identify near-duplicate questions
- support smarter replacements
- improve quality review

### 9.7 Notes-to-Question Generation
Used in: `backend/notes_processor.py`

Process:
- extract raw text from uploaded notes
- clean and split text into sentences
- find keywords
- convert sentence content into generated questions

### 9.8 Optional OpenAI-Based Generation
Used in: `backend/ai_integration.py`

Purpose:
- generate better question drafts from uploaded notes
- provide AI chat support

This is optional and requires:
- `OPENAI_API_KEY`

## 10. Why This Project Is AI/ML-Based
This project is AI/ML-based because:
- it predicts question difficulty using ML
- it ranks questions intelligently using a scoring model
- it extracts information from notes and converts it into draft questions
- it supports similarity and recommendation logic
- it optionally integrates LLM-based generation and AI chat

## 11. Project Workflow from Start to End
### Step 1: System Startup
- backend starts with FastAPI
- database connection is created
- schema migration runs
- seed dataset loads from `data/questions_seed.json`
- ML model is trained on the stored questions

### Step 2: Question Bank Preparation
Questions enter the system through:
- startup seed file
- manual question entry
- JSON/CSV bulk import
- uploaded notes
- optional AI notes generation

### Step 3: Faculty Chooses Exam Parameters
User selects:
- department
- subject
- topic
- subtopic
- difficulty
- marks
- question types
- exam type
- number of variants

### Step 4: Question Filtering
The backend filters the database according to selected metadata.

### Step 5: ML-Based Ranking
Each filtered question is scored using:
- metadata match
- ML-predicted difficulty
- quality
- times used
- verification status

### Step 6: Exact Mark Selection
The system searches for an exact combination of questions matching total marks.

### Step 7: Paper Variant Generation
Multiple variants are created and stored in the database.

### Step 8: Analytics and Review
The system displays:
- topic distribution
- difficulty distribution
- review queue
- quality review
- paper comparison

## 12. Flowchart
```mermaid
flowchart TD
    A[Start Application] --> B[Connect Database]
    B --> C[Run Schema Migration]
    C --> D[Load Seed Dataset]
    D --> E[Train ML Model]
    E --> F[User Opens Dashboard]
    F --> G[Select Department, Subject, Topic, Difficulty, Marks]
    G --> H[Fetch Matching Questions from DB]
    H --> I[ML Difficulty Prediction + Heuristic Scoring]
    I --> J[Exact Marks Combination Search]
    J --> K[Generate Paper Variants]
    K --> L[Store Papers in Database]
    L --> M[Display Output, Analytics, Review]
```

## 13. Block Diagram
```mermaid
flowchart LR
    U[User / Faculty] --> F[Frontend Dashboard]
    F --> A[FastAPI Backend]
    A --> D[(PostgreSQL Database)]
    A --> M[ML Model - Random Forest]
    A --> N[Notes Processor]
    A --> O[Similarity Engine]
    A --> P[Optional OpenAI API]
    D --> A
    M --> A
    N --> A
    O --> A
    P --> A
    A --> F
```

## 14. Sample Database Entries
### Example question entry
- department: Computer Science Engineering
- subject: Database Management Systems
- topic: Transactions
- subtopic: ACID Properties
- difficulty: Medium
- marks: 5
- type: Short
- bloom_level: Apply
- course_outcome: CO-1

### Example generated paper entry
- title: Faculty Examination Set
- exam_type: End-Sem
- total_marks: 60
- variant_number: 1
- created_by: Faculty User
- pattern_used: AI balanced selection

## 15. API Endpoints Summary
Important endpoints:
- `GET /filters`
- `GET /dashboard-summary`
- `GET /questions`
- `POST /add-question`
- `POST /import-questions`
- `POST /import-file`
- `POST /generate-paper`
- `GET /analysis`
- `GET /generated-papers`
- `POST /upload-notes`
- `POST /upload-notes-ai`
- `GET /review-queue`
- `GET /question-quality-review`
- `GET /questions/{id}/similar`
- `GET /questions/{id}/alternatives`
- `GET /compare-papers`
- `POST /auth/register`
- `POST /auth/login`
- `GET /blueprints`
- `POST /blueprints`
- `POST /chat`

## 16. Deep Learning Extension Ideas
The current system uses classical ML, but it can be extended to deep learning by:
- using sentence embeddings for semantic similarity
- using transformers for topic classification
- using deep learning for automated answer generation
- using LSTM/Transformer models for text understanding
- replacing heuristic notes generation with sequence-to-sequence models

## 17. Viva / Teacher Questions and Answers
### Q1. What is the main aim of this project?
To automate the process of question bank management and question paper generation using AI/ML-assisted selection and analytics.

### Q2. Which database is used?
PostgreSQL is the intended main database. SQLAlchemy ORM is used for DB operations.

### Q3. Which ML algorithm is used?
Random Forest Classifier from Scikit-learn.

### Q4. Why Random Forest?
Because it works well for structured tabular data, handles categorical + numerical features, is stable, and is easy to explain academically.

### Q5. Is this a deep learning project?
The current implementation is an AI/ML project using classical ML. It is highly relevant to AIML and can be extended to deep learning for semantic analysis and advanced question generation.

### Q6. How does paper generation happen?
The system filters questions, scores them, predicts difficulty, searches exact mark combinations, generates variants, and stores them.

### Q7. How is duplicate control handled?
Using similarity detection and alternative suggestion logic.

### Q8. What is the role of the notes upload feature?
It converts chapter notes or unit notes into draft questions automatically.

### Q9. What is the role of OpenAI integration?
Optional AI support for better question generation from uploaded notes and AI assistant chat.

### Q10. What is approval workflow?
Questions can remain in draft, be reviewed, and be marked approved or rejected.

### Q11. What is the use of `times_used`?
It reduces repeated use of the same question in generated papers.

### Q12. What is Bloom level used for?
To classify the cognitive level of a question, which helps academic quality and outcome-based education mapping.

### Q13. What is blueprint builder?
It allows faculty to define exact paper patterns such as marks allocated to MCQ, Short, and Long questions.

### Q14. What is paper comparison?
It measures overlap between generated papers to analyze similarity.

### Q15. Why is SQLAlchemy used?
It provides ORM abstraction, cleaner code, model mapping, and easier maintenance.

## 18. Strengths of the Project
- modular code structure
- AI/ML integration
- structured database design
- support for analytics and review workflow
- notes-based question generation
- optional LLM integration
- multiple paper variants
- modern dashboard UI

## 19. Limitations
- current ML model is classical, not deep neural
- similarity detection is text-ratio based, not embedding based
- OpenAI features require a valid API key
- exact mark generation may still depend on dataset richness

## 20. Future Scope
- transformer-based semantic similarity
- deep-learning-based topic and answer generation
- faculty login with secure token auth
- advanced approval workflow
- richer chart dashboard
- Word export
- automatic answer evaluation
- outcome coverage heatmaps

## 21. How to Run the Project from CMD Terminal
Open `cmd` and run:

```cmd
cd /d "C:\Users\purab\Documents\New project"
venv\Scripts\activate.bat
set DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/question_paper_db
uvicorn backend.main:app --reload
```

If you want optional OpenAI features:

```cmd
set OPENAI_API_KEY=YOUR_REAL_OPENAI_KEY
set OPENAI_MODEL=gpt-5-mini
```

Then open:
- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

## 22. Conclusion
Smart AI Question Paper Generator is a strong AI/ML-based educational automation project. It combines database engineering, API development, machine learning, frontend design, workflow automation, and optional LLM capabilities into one practical academic system. It is highly suitable for presentation in AIML and Deep Learning subjects because it demonstrates applied intelligence, structured problem solving, real-world usefulness, and future scalability toward advanced deep learning methods.

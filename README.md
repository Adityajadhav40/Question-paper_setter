# Smart AI Question Paper Generator

🚀 Smart AI Question Paper Generator

An AI/ML-powered academic automation system that generates balanced question papers using machine learning, structured databases, and intelligent selection algorithms.

📌 Overview

The Smart AI Question Paper Generator is a full-stack system designed to automate the process of creating exam papers. It eliminates manual effort by intelligently selecting questions based on difficulty, topic distribution, and exam patterns.

The system integrates:

📊 Machine Learning for difficulty prediction
🧠 Heuristic algorithms for smart selection
📚 Notes-to-question generation
📈 Analytics and review workflows
🎯 Key Features

✅ Automatic Question Paper Generation
✅ AI-based Difficulty Prediction (ML Model)
✅ Multiple Paper Variants Generation
✅ Question Bank Management (CRUD + Import)
✅ Notes → Question Generation (PDF/DOCX/TXT)
✅ Duplicate Question Detection
✅ Blueprint-based Paper Design
✅ Analytics Dashboard
✅ Faculty Review & Approval Workflow
✅ Optional AI (LLM) Integration

🧠 AI / ML Concepts Used
Random Forest Classifier (Difficulty Prediction)
Feature Engineering on Question Metadata
Heuristic Scoring Algorithm
Text Similarity Detection
Notes-to-Question NLP Processing
Optional LLM-based Question Generation
🏗️ Tech Stack
Backend
Python
FastAPI
Uvicorn
Database
PostgreSQL
SQLAlchemy ORM
Machine Learning
Scikit-learn
RandomForestClassifier
OneHotEncoder
ColumnTransformer
Frontend
HTML, CSS, JavaScript
Chart-based Visualization
Utilities
pypdf (PDF parsing)
python-docx (DOCX parsing)
requests (API calls)
⚙️ System Workflow
🚀 System starts → DB + ML model initialized
📚 Question bank is loaded/imported
👨‍🏫 User selects exam parameters
🔍 Questions are filtered
🧠 ML predicts difficulty
📊 Heuristic scoring ranks questions
🧩 Exact marks combination is generated
📝 Paper variants are created
📈 Analytics & review displayed
📂 Project Structure
backend/
│── main.py              # FastAPI entry point
│── database.py          # DB connection
│── models.py            # Tables definition
│── generator.py         # Paper generation engine
│── ml_model.py          # ML model training
│── notes_processor.py   # Notes to questions
│── similarity.py        # Duplicate detection
│── ai_integration.py    # Optional AI (OpenAI)
│
data/
│── questions_seed.json  # Initial dataset
🧩 Core Modules
🔹 Generator Engine
Selects best questions
Maintains difficulty & type balance
Ensures exact marks matching
🔹 ML Module
Predicts difficulty using Random Forest
🔹 Notes Processor
Converts notes → questions
🔹 Similarity Engine
Detects duplicate/near-duplicate questions
🔹 API Layer
REST endpoints for all operations
📊 Algorithms Used
✔ Random Forest Classifier
Predicts question difficulty
Works well with structured data
✔ Heuristic Scoring
Scores questions based on:
Topic match
Difficulty match
Usage count
Quality score
✔ Backtracking (Subset Sum)
Finds exact marks combination
✔ Similarity Matching
Detects duplicate questions
🔌 API Endpoints (Sample)
GET /questions
POST /add-question
POST /generate-paper
POST /upload-notes
GET /analysis
GET /generated-papers
POST /auth/login
▶️ How to Run
1. Clone Repository
git clone https://github.com/your-username/project-name.git
cd project-name
2. Setup Environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
3. Configure Database
set DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/question_paper_db
4. Run Server
uvicorn backend.main:app --reload
5. Open in Browser
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
🤖 Optional AI Setup
set OPENAI_API_KEY=YOUR_API_KEY
set OPENAI_MODEL=gpt-5-mini
💡 Use Cases

👨‍🏫 Faculty → Generate exam papers quickly
🏫 Colleges → Standardized exam creation
📚 Students → Practice paper generation
📊 Admin → Analytics & monitoring

🚀 Future Scope
Transformer-based NLP models
Semantic similarity using embeddings
Auto answer generation
Word/PDF export
Advanced dashboard analytics
Secure authentication system
⚠️ Limitations
Uses classical ML (not deep learning yet)
Similarity is basic (not embedding-based)
Requires good dataset quality
AI features need API key
🏆 Why This Project Stands Out

✔ Combines AI + Backend + Database + NLP
✔ Real-world academic problem solving
✔ Scalable and modular architecture
✔ Strong for AIML + Hackathon + Placements

📌 Conclusion

This project demonstrates how AI/ML can be applied in real-world academic systems. It automates question paper generation using intelligent algorithms, structured data, and scalable architecture, making it highly relevant for modern educational institutions.

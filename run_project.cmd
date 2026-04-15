@echo off
cd /d "C:\Users\purab\Documents\New project"
call venv\Scripts\activate.bat
if "%DATABASE_URL%"=="" (
  echo Please set DATABASE_URL before running this script.
  echo Example:
  echo set DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/question_paper_db
  exit /b 1
)
uvicorn backend.main:app --reload

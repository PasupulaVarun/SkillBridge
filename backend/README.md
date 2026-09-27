# SkillBridge Backend v2

FastAPI backend for the SkillBridge Academia × Industry Collaboration Portal.

## Local run
cd backend
python -m venv .venv
pip install -r requirements.txt
uvicorn main:app --reload

Open http://127.0.0.1:8000/docs.

Seed demo content:
curl -X POST http://127.0.0.1:8000/api/seed

## Database
SQLite is the zero-setup default. Docker Compose provides PostgreSQL + pgvector.

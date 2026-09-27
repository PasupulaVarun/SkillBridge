# SkillBridge — Academia × Industry Collaboration Portal

A full-stack SIH-ready platform connecting **Students, Academicians, Industries and Institutions** through skill profiling, intelligent opportunity matching, collaboration and analytics.

## v10 release
- Responsive dark glassmorphism frontend
- Role-based authentication and session tokens
- Student assessment, skill profile, recommendations and applications
- Learning hub and digital portfolio
- Industry opportunity publishing and candidate discovery
- Academician collaboration surfaces
- Institution analytics and reports
- Explainable matching: direct coverage + semantic/synonym similarity + technical + soft skills
- SQLite local development
- PostgreSQL + pgvector Docker path
- FastAPI interactive docs

## Run locally
```bash
cd backend
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` for API docs. In another terminal, serve the frontend with `python -m http.server 5500` from the project root and open `http://127.0.0.1:5500`.

Seed demo data:
```bash
curl -X POST http://127.0.0.1:8000/api/seed
```

## Docker
```bash
docker compose up --build
```

This starts PostgreSQL/pgvector and the FastAPI service.

## Repository structure
```text
SkillBridge/
├── index.html
├── styles.css
├── app.js
├── api.js
├── backend/
│   ├── main.py
│   ├── embedding_service.py
│   ├── requirements.txt
│   └── Dockerfile
├── tests/
│   └── smoke_test.py
└── docker-compose.yml
```

## Production hardening
Before public deployment, add HTTPS, secure HTTP-only cookies, secret management, rate limiting, audit logging, Alembic migrations, email verification/password reset, object storage for documents, and persistent pgvector-backed embeddings.

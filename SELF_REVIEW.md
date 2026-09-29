# SkillBridge Release Review

## v11 Persistence + security
- User records persist in PostgreSQL through SQLAlchemy.
- Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes; plaintext passwords are never stored.
- Sessions are server-side and delivered through an HttpOnly, Secure, SameSite=None cookie.
- Frontend no longer stores bearer authentication tokens in localStorage.
- Password change invalidates existing sessions.
- CORS is restricted through FRONTEND_ORIGIN rather than wildcard credentials.

## v11 Domain completeness
- Student: assessment, profile, recommendations, applications, learning, portfolio, collaboration.
- Industry: opportunity publishing, candidate discovery, application pipeline and collaboration.
- Academician: research, training, mentorship and industry collaboration surfaces.
- Institution: skill-supply/demand analytics and reporting.
- Shared account area: authenticated identity, role and organization context.

## Remaining production backlog
- Alembic migrations for schema evolution.
- Email verification and password reset.
- Rate limiting and audit logging.
- Object/document storage.
- pgvector-backed embedding persistence and semantic retrieval.

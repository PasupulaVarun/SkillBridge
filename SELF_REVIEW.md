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

## v13 Live Market + UX release
- Added dedicated Student Live Market navigation.
- Added external job-feed endpoint with five-minute cache.
- Added Adzuna integration path via environment credentials, with public-feed fallback.
- External listings are visibly labelled by source and timestamp.
- Added skill-aware market queries based on the student's profile.
- Added credentialed cross-origin API requests for HttpOnly session authentication.
- Added responsive live-market presentation.
- Kept external market listings separate from internal SkillBridge opportunities.
- Frontend deployment triggered from commit 0b7955094c2eba996f250450527c659c4e4f99ce.

### Next production upgrades
- Configure an India-focused/licensed market-data provider.
- Add server-side pagination/filtering and saved searches.
- Add WebSocket/SSE notifications for application status and new matches.
- Add email verification/password reset and rate limiting.
- Replace heuristic matching with persisted pgvector embeddings.

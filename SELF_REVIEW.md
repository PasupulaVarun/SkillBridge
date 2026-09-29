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

## v15 Production engineering layers
- pgvector dependency added and the API creates the PostgreSQL vector extension when the database permits it.
- Opportunity semantic documents persist embeddings using a 1536-dimension vector and expose `/api/semantic-search` with lexical fallback when embeddings are not configured.
- Notification records persist in PostgreSQL with unread/read state and read-all support.
- Application submissions/status changes and new opportunities create durable notification records.
- `/api/notifications/stream` provides authenticated Server-Sent Events for live notification delivery.
- Frontend opens the SSE stream with credentials, reconnects after transient failures, and exposes a persistent Notifications page.
- Live employment-market integration is now explicitly India-scoped through `ADZUNA_COUNTRY=in`; public non-India fallback was removed. Adzuna credentials remain required for external market listings.
- Existing internal SkillBridge opportunities remain separate from external market listings.
- Duplicate `/api/opportunities` route was removed during self-review.

### Deployment/configuration notes
- `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` must be supplied in Render for licensed external job data to appear.
- `OPENAI_API_KEY` must be supplied in Render to generate semantic embeddings; without it, the system stays operational and uses lexical matching.
- The Render Postgres account must permit the `vector` extension; the API logs a clear capability message if it cannot enable it.
- Alembic migrations, rate limiting, email verification/password reset, audit logging, and background embedding workers remain separate hardening work for a later production phase.

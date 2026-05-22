# LLM-Powered Research Assistant API

A Django-based SaaS backend that lets users submit a company name, run an async research workflow, and generate structured investment-style reports powered by grounded data and an LLM.

The project includes:
- JWT authentication
- free/pro subscription tiers
- async research jobs with Celery
- grounded company context from Wikipedia, Yahoo Finance, and NewsAPI
- Claude-powered structured report generation
- embeddings and semantic search
- usage logging and monthly free-tier limits
- retrying failed research jobs
- report bookmarking, analyst notes, and export
- usage dashboard summary
- browser UI for registration, login, and job submission

## What You Get

User flow:
1. A user opens the website.
2. They register or log in.
3. They submit a company name like `Tesla` or `OpenAI`.
4. The system creates a `ResearchJob`.
5. The research pipeline gathers context and asks the LLM for a strict JSON report.
6. The report is stored and can later be searched semantically.

Core apps:
- `users`: auth, profile, subscription tier
- `research`: job creation, job status, Celery task orchestration
- `reports`: generated report storage and semantic search
- `usage`: API usage logs and LLM token tracking

## Current Local Behavior

The repo is currently set up for easy local development:
- SQLite is used locally
- Celery runs in eager mode locally, so jobs execute immediately inside the Django request cycle
- the home page at `/` provides a browser UI
- if `CLAUDE_API_KEY` is missing, research jobs still get created but will end in `failed`

This means you can test the full auth and job flow immediately, even before wiring real external API keys.

## Browser UI

Open:

```text
http://127.0.0.1:8000/
```

The page lets you:
- register a user
- log in
- load your profile
- create a research job
- poll job status
- retry failed jobs
- list reports
- bookmark reports
- save analyst notes
- export reports as markdown
- load usage summary
- run semantic search

Health endpoint:

```text
http://127.0.0.1:8000/api/health/
```

## API Endpoints

Auth:
- `POST /api/users/register/`
- `POST /api/users/login/`
- `POST /api/users/token/refresh/`
- `GET /api/users/me/`

Research:
- `GET /api/research/jobs/`
- `POST /api/research/jobs/`
- `GET /api/research/jobs/<job_id>/`
- `POST /api/research/jobs/<job_id>/retry/`

Reports:
- `GET /api/reports/`
- `GET /api/reports/<id>/`
- `PATCH /api/reports/<id>/organize/`
- `GET /api/reports/<id>/export/?file_format=md`
- `GET /api/reports/search/?query=...`
- `GET /api/search/?query=...`

Utility:
- `GET /api/health/`
- `GET /api/usage/summary/`

All endpoints except register, login, refresh, and health require authentication.

## Local Setup

### 1. Create the virtual environment

```powershell
python -m venv venv
```

### 2. Activate it

```powershell
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Create `.env`

Copy the example file:

```powershell
Copy-Item .env.example .env
```

For local development, use a config like this:

```env
DJANGO_SECRET_KEY=dev-only-local-secret-key-change-this-123456
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
NEWSAPI_KEY=
CLAUDE_API_KEY=
CLAUDE_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_URL=https://api.anthropic.com/v1/messages
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
FREE_TIER_MONTHLY_REPORT_LIMIT=5
CELERY_TASK_ALWAYS_EAGER=True
CELERY_TASK_EAGER_PROPAGATES=False
USE_PGVECTOR=False
PGVECTOR_INDEX_LISTS=100
DB_CONN_MAX_AGE=60
CSRF_TRUSTED_ORIGINS=
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
SECURE_REFERRER_POLICY=same-origin
```

Notes:
- leave `CLAUDE_API_KEY` empty only if you want to test the app flow without actual report generation
- add a real `NEWSAPI_KEY` if you want live news enrichment

### 5. Run migrations

```powershell
python manage.py migrate
```

### 6. Start the app

```powershell
python manage.py runserver 127.0.0.1:8000
```

Then open:

```text
http://127.0.0.1:8000/
```

## Local Demo Account

If you already created the demo account during setup, the local credentials are:

- username: `demo`
- password: `StrongPass123!`

If that user does not exist in your database, just register a new one from the website.

## How to Use the App

### Register

From the website:
1. Open `/`
2. Fill the `Register` form
3. Click `Create Account`

### Login

1. Fill the `Login` form
2. Click `Log In`
3. The page stores the access token in browser local storage

### Submit a research job

1. Enter a company name like `Tesla`
2. Click `Start Research`
3. Copy or reuse the returned job ID
4. Click `Check Status` to poll the job

### Retry a failed job

1. Paste the failed job ID into the job ID box
2. Click `Retry Failed Job`

### Organize and export a report

1. Load or create a report
2. Paste the report ID into the report ID box
3. Add analyst notes and click `Save Bookmark & Notes`
4. Click `Export Markdown` to load the downloadable report text

### View usage summary

1. Click `Usage Summary`
2. Review monthly usage, job counts, report counts, and token totals

### Expected statuses

- `pending`: job created
- `processing`: research is running
- `completed`: report generated
- `failed`: research failed, often because an API key is missing

## Why a Job May Fail Locally

Common causes:
- `CLAUDE_API_KEY is not configured.`
- no internet access for external data sources
- invalid API key
- malformed response from an external service

If `CLAUDE_API_KEY` is missing, this is expected:
- job creation still succeeds
- status polling works
- final status becomes `failed`

## If You Cannot Run a Research Job

If you are able to log in and click `Start Research` but no report is generated, this usually means the job was created successfully but failed during LLM processing.

Typical flow:
1. You register
2. You log in
3. You submit a company name
4. The job is created
5. The job later shows `failed`

The most common reason is:

```text
CLAUDE_API_KEY is not configured.
```

### How to make research jobs work

Open [.env](/d:/LLM-Powered%20Research%20Assistant%20API/.env) and set:

```env
CLAUDE_API_KEY=your_real_claude_api_key_here
NEWSAPI_KEY=your_real_newsapi_key_here
```

Then restart the Django server:

```powershell
venv\Scripts\Activate.ps1
python manage.py runserver 127.0.0.1:8000
```

After restarting:
1. Open `http://127.0.0.1:8000/`
2. Log in
3. Submit a new company name such as `Tesla`
4. Poll the job status

### Important note

Without a real `CLAUDE_API_KEY`:
- job creation works
- job polling works
- real report generation does not work

So if your research job is not completing, check the job status first. If the error mentions Claude or API key configuration, the backend is working and only the LLM credential is missing.

## Running with Real Report Generation

To generate real reports:
1. set a valid `CLAUDE_API_KEY` in `.env`
2. optionally set `NEWSAPI_KEY`
3. restart the Django server
4. submit a new research job

Then the system will:
- fetch Wikipedia summary
- fetch Yahoo Finance data if available
- fetch recent news if a NewsAPI key is present
- call Claude for strict JSON report generation
- store the report and embedding

## Celery and Redis

### Local development

By default, this repo currently uses:

```env
CELERY_TASK_ALWAYS_EAGER=True
```

That means:
- you do not need Redis locally just to test the workflow
- tasks run immediately in-process

### More realistic local async mode

If you want true async behavior:

1. change `.env`:

```env
CELERY_TASK_ALWAYS_EAGER=False
CELERY_TASK_EAGER_PROPAGATES=True
REDIS_URL=redis://localhost:6379/0
```

2. start Redis
3. start a Celery worker

On Windows:

```powershell
celery -A research_assistant_api worker -l info --pool=solo
```

## PostgreSQL and pgvector

The app supports two search modes:

### Local/simple mode

- database: SQLite
- embeddings stored in JSON
- cosine similarity computed in Python

### Production/vector mode

- database: PostgreSQL
- `USE_PGVECTOR=True`
- embeddings also stored in `embedding_vector`
- search can run in the database using pgvector

Recommended production env values:

```env
DATABASE_URL=postgres://user:password@host:5432/research_db
USE_PGVECTOR=True
CELERY_TASK_ALWAYS_EAGER=False
```

After switching to PostgreSQL:

```powershell
python manage.py migrate
```

The migration creates:
- the `vector` extension if available
- a pgvector IVFFlat index for report embeddings

## Production Security Settings

For production, set:

```env
DEBUG=False
ALLOWED_HOSTS=your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

Also deploy behind:
- Nginx
- an HTTPS reverse proxy or load balancer

## Deployment

Deployment assets are included in:
- [deploy/nginx.conf](/d:/LLM-Powered%20Research%20Assistant%20API/deploy/nginx.conf)
- [deploy/gunicorn.service](/d:/LLM-Powered%20Research%20Assistant%20API/deploy/gunicorn.service)
- [deploy/celery.service](/d:/LLM-Powered%20Research%20Assistant%20API/deploy/celery.service)

Production stack:
- Django
- Gunicorn
- Nginx
- Celery
- Redis
- PostgreSQL
- optional pgvector

CI is configured in:
- [.github/workflows/ci.yml](/d:/LLM-Powered%20Research%20Assistant%20API/.github/workflows/ci.yml)

## Testing

Run:

```powershell
python manage.py check
pytest
```

What is covered:
- auth protection
- register/login/refresh flow
- research job creation
- failed job retry
- Celery task state transition
- free-tier limit enforcement
- report access and search
- report organization and export
- usage logging
- usage summary dashboard
- embedding helpers

## Troubleshooting

### `/` shows 404 or old content

- restart `runserver`
- hard refresh the browser with `Ctrl + F5`

### Job stays `failed`

Check:
- `CLAUDE_API_KEY`
- internet access
- external API availability

### Login works but research does not

This usually means:
- auth is fine
- job system is fine
- LLM credentials are missing or invalid

### PostgreSQL connection refused

Your `DATABASE_URL` is pointing to a Postgres server that is not running.

Use SQLite locally:

```env
DATABASE_URL=sqlite:///db.sqlite3
USE_PGVECTOR=False
```

## Project Status

Implemented:
- JWT auth
- protected endpoints
- user tiers
- monthly free-tier cap
- usage logging
- usage dashboard summary
- research job model and status polling
- failed job retry
- grounded data gathering
- Claude integration
- structured report persistence
- report bookmarking and analyst notes
- report export
- embeddings and semantic search
- browser UI for registration/login/job submission
- tests, CI, and deployment scaffolding

Operational requirements for full real output:
- valid `CLAUDE_API_KEY`
- optional `NEWSAPI_KEY`
- internet access
- Redis and Celery if you want real async mode
- PostgreSQL if you want pgvector in production

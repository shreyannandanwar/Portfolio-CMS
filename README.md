# Portfolio CMS

A self-hosted portfolio and blog system built with Flask — because WordPress was overkill and static sites weren't enough.

This isn't a template. It's a production-grade CMS I built to understand every layer of the stack that frameworks usually hide: session management, API rate limiting, security headers, blueprint architecture, and deployment configuration. The portfolio you're reading this from runs on it.

---

## Why I built this

Most developer portfolios either use a bloated CMS or a static site generator. I wanted something in between — a system I fully understand, can extend, and can deploy anywhere. Building it from scratch meant confronting real production concerns: caching strategies, authentication flows, database connection pooling, and security hardening that actually matters.

---

## Architecture

The application follows a clean, modular Flask structure designed for maintainability and testability.

```
portfolio/
├── app/
│   ├── __init__.py        # Application factory — enables env-based config and test isolation
│   ├── config.py          # Dev / Prod / Test configurations
│   ├── models/            # SQLAlchemy ORM — explicit relationships and constraints
│   ├── services/          # Business logic separated from route handlers
│   │   ├── github.py      # GitHub API sync with caching layer
│   │   ├── markdown.py    # Markdown processing and sanitization
│   │   └── images.py      # Upload handling and optimization
│   ├── admin/             # Admin blueprint — auth-gated CMS interface
│   ├── public/            # Public blueprint — all user-facing routes
│   └── utils/             # Security headers, logging, error handling
├── tests/                 # Isolated test suite (SQLite in-memory)
└── run.py
```

**Key decisions:**

- **Application factory pattern** — configuration injected at runtime, not hardcoded. Makes environment switching and test isolation clean.
- **Blueprint separation** — `public` and `admin` blueprints are entirely independent. Admin routes are mounted at an obscured path and protected behind session auth.
- **Service layer** — business logic lives in `services/`, not in route handlers. Routes handle HTTP; services handle work. This makes both testable in isolation.

---

## Interesting problems solved

**GitHub API rate limiting**
The GitHub public API limits unauthenticated requests to 60/hour. Fetching repo data on every page load would exhaust this quickly on any real traffic. I built an internal caching layer that stores repo metadata on first fetch and serves from cache on subsequent requests, with a manual refresh trigger in the admin panel. The tradeoff: data is slightly stale, but the site stays fast and the API budget stays intact.

**Security headers without a framework**
Rather than relying on a security extension, I implemented CSP, HSTS, X-Frame-Options, and X-Content-Type-Options manually in a `utils/security.py` middleware. Writing them by hand meant understanding exactly what each header does and why — useful when something breaks in production.

**Test isolation**
The test suite runs against an in-memory SQLite database with CSRF disabled. Each test gets a clean application context. This keeps tests fast, deterministic, and independent of the development database.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python · Flask · SQLAlchemy |
| Database | PostgreSQL (prod) · SQLite (dev/test) |
| Auth | bcrypt · HTTP-only session cookies |
| Frontend | Jinja2 · Tailwind CSS |
| Testing | pytest · pytest-cov |
| Deployment | gunicorn · nginx |

---

## Running locally

```bash
git clone https://github.com/shreyannandanwar/portfolio
cd portfolio
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///instance/portfolio.db
GITHUB_USERNAME=your-github-username
ADMIN_URL_PREFIX=/admin
```

```bash
python init_db.py
python create_admin.py
python run.py
# → http://localhost:5000
```

**Tests:**

```bash
pytest --cov=app tests/
```

---

## Security

- CSRF protection on all forms
- bcrypt password hashing with salt
- HTTP-only, secure session cookies
- CSP, HSTS, X-Frame-Options, X-Content-Type-Options headers
- HTML sanitization on user-submitted content
- Admin panel mounted at an obscured, configurable URL path

---

## Deployment (production)

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app('production')"
```

Minimal nginx config:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/portfolio/app/static;
        expires 30d;
    }
}
```

Production environment variables:

```env
FLASK_ENV=production
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://user:pass@localhost/dbname
ADMIN_URL_PREFIX=/your-obscured-path
LOG_LEVEL=WARNING
```

---

## What I'd do differently

Separate the content model from presentation more cleanly — a headless CMS approach with a proper API layer would make the frontend more flexible. I'd also invest earlier in deployment automation and environment configuration management rather than bolting it on at the end.

---

*Part of my portfolio at [shreyannandanwar.dev](https://shreyannandanwar.dev)*
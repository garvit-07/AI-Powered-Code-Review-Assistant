# AI-Powered Code Review Assistant

An async **FastAPI** service that sends submitted code to a **GenAI model** and returns structured JSON feedback on bugs, style, and best practices. Every review is stored in **PostgreSQL**, so each user has a private review history. A lightweight web UI is included.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Async-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![License](https://img.shields.io/badge/License-MIT-green)

## 📸 Screenshots

| Sign In | Paste Code |
|:---:|:---:|
| ![Sign In](docs/images/01-sign-in.png) | ![Paste Code](docs/images/02-paste-code.png) |

### Review Results

Flagged lines are color-coded in the code, and every finding card explains the problem and suggests a fix.

![Review Feedback](docs/images/03-review-feedback.png)

### Interactive Findings

Click a finding to jump to its corresponding line. You can also click a flagged line to navigate to its finding.

![Line-Linked Finding](docs/images/04-line-linked-finding.png)

> The screenshots show the real UI in `app/static/index.html`, rendered with sample data.

## ✨ Features

- **Structured output:** The model returns JSON containing a summary, a score from 0–100, and findings with line number, category, severity, title, explanation, and suggestion. Pydantic validates the response, with one automatic retry if the JSON is malformed.
- **Fully asynchronous:** Built with FastAPI, SQLAlchemy 2.0 async sessions, `asyncpg`, and the asynchronous Anthropic client. Password hashing runs in a worker thread to avoid blocking the event loop.
- **Private review history:** JWT authentication ensures users can list, open, and delete only their own reviews. Requests for another user's review ID return `404`.
- **Works without an API key:** If no API key is configured, a deterministic rule-based reviewer is used, allowing you to try the project immediately.
- **Provider-agnostic design:** The LLM is accessed through a small `Reviewer` interface in `app/services/llm.py`.
- **Safe by default:** Submitted code is treated as untrusted input, code length is capped, and model output is escaped in the UI.

## 🏗️ How It Works

```mermaid
sequenceDiagram
    participant U as Browser
    participant A as FastAPI
    participant L as GenAI Model
    participant D as PostgreSQL

    U->>A: POST /api/reviews (JWT + code)
    A->>L: System prompt + line-numbered code
    L-->>A: JSON feedback
    A->>A: Validate with Pydantic
    Note right of A: Retry once if invalid
    A->>D: INSERT review (feedback stored as JSONB)
    A-->>U: 201 Created + structured review

    U->>A: GET /api/reviews
    A->>D: SELECT reviews WHERE user_id = current user
    D-->>A: User's review history
    A-->>U: Review history
```

## 📁 Project Structure

```text
ai-code-review-assistant/
├── app/
│   ├── main.py                  # App factory, lifespan, static UI
│   ├── core/
│   │   ├── config.py            # Environment settings
│   │   └── security.py          # Password hashing and JWT helpers
│   ├── db/
│   │   ├── base.py              # SQLAlchemy declarative base
│   │   └── session.py           # Async engine and DB dependency
│   ├── models/                  # User and Review models
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── services/
│   │   └── llm.py               # Reviewer implementations and JSON parsing
│   ├── api/
│   │   ├── deps.py              # Current-user dependency
│   │   └── routes/
│   │       ├── auth.py          # Authentication endpoints
│   │       └── reviews.py       # Review endpoints
│   └── static/
│       └── index.html           # Web UI
├── tests/                       # Pytest and API tests
├── docs/
│   └── images/                  # README screenshots
├── .github/
│   └── workflows/
│       └── ci.yml               # CI workflow
├── Dockerfile
├── docker-compose.yml           # API + PostgreSQL
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
└── .env.example
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker Desktop and Docker Compose (recommended)
- An Anthropic API key for AI-powered reviews (optional; the rule-based reviewer works without one)

### Option A: Docker (Recommended)

**1. Clone the repository**

Replace `YOUR_USERNAME` with your GitHub username.

```bash
git clone https://github.com/YOUR_USERNAME/AI-Powered-Code-Review-Assistant.git
cd AI-Powered-Code-Review-Assistant
```

**2. Configure environment variables**

```bash
cp .env.example .env
```

Edit `.env` and configure your `SECRET_KEY`, database settings, and optional `ANTHROPIC_API_KEY`.

Generate a secure secret key with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**3. Start the application**

```bash
docker compose up --build
```

Once the containers are running, open:

- **Web UI:** http://localhost:8000
- **Interactive API docs:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

These URLs assume the Docker Compose configuration exposes the API on port `8000`.

### Option B: Run Locally

**1. Create and activate a virtual environment**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

For macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

**2. Install dependencies**

```bash
pip install -r requirements-dev.txt
```

**3. Configure the environment**

Create your `.env` file from `.env.example` and update the database URL and secret key.

For example, the application expects an asynchronous PostgreSQL URL similar to:

```text
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/code_review
```

Ensure PostgreSQL is running and the database exists before starting the application.

**4. Start the server**

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000 to access the UI.

> Database tables are created automatically at startup. This is convenient for development; production deployments should use database migrations.

## ⚙️ Configuration

Configure the following variables in your `.env` file.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/code_review` | Asynchronous PostgreSQL connection URL |
| `SECRET_KEY` | `change-me-in-production` | JWT signing key; replace with a secure random value |
| `LLM_PROVIDER` | `anthropic` | Selects the `anthropic` or `mock` provider |
| `ANTHROPIC_API_KEY` | Empty | Optional API key; without it, the rule-based reviewer is used |
| `LLM_MODEL` | `claude-sonnet-4-6` | Model used for code reviews |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Access token lifetime in minutes |

Check `.env.example` and `app/core/config.py` for the exact configuration supported by your current code.

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register a new account |
| `POST` | `/api/auth/login` | Log in and obtain a JWT |
| `GET` | `/api/auth/me` | Get the current authenticated user |
| `POST` | `/api/reviews` | Review code and save the result |
| `GET` | `/api/reviews?limit=30&offset=0` | List review history |
| `GET` | `/api/reviews/{id}` | Retrieve a single review |
| `DELETE` | `/api/reviews/{id}` | Delete a review |
| `GET` | `/health` | Check application health |

The login endpoint accepts form fields named `username` (the user's email) and `password`.

## 💻 Example API Request

After registering and logging in, use the returned access token to submit code for review.

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -d "username=you@example.com&password=password123" \
  | jq -r .access_token)

curl -X POST http://localhost:8000/api/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "code": "def f(x, items=[]):\n    try:\n        pass\n    except:\n        print(\"x\")"
  }'
```

### Example Response

```json
{
  "id": 1,
  "language": "python",
  "model": "claude-sonnet-4-6",
  "feedback": {
    "summary": "Shared mutable default and a bare except hide real problems.",
    "score": 58,
    "findings": [
      {
        "line": 1,
        "category": "bug",
        "severity": "high",
        "title": "Mutable default argument",
        "explanation": "The default list is shared between calls.",
        "suggestion": "Use items=None and create the list inside the function."
      }
    ]
  },
  "created_at": "2026-10-10T08:12:00Z"
}
```

> This is an illustrative response. Exact fields and values depend on your implementation and reviewer.

## 🧪 Testing

Install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the test suite:

```bash
pytest -q
```

Tests use in-memory SQLite and a mock reviewer, so they do not require PostgreSQL or an external AI API key.

The test suite covers registration, login, authentication guards, structured feedback, input limits, JSON parsing, and isolation of review histories between users.

## 🧠 Design Decisions

- **JSONB for feedback:** Findings are stored together as structured JSON, avoiding extra joins when retrieving reviews. A separate findings table may be useful if cross-review finding queries become important.
- **Line-numbered prompts:** Submitted code is numbered (`1: ...`, `2: ...`) to help the model reference specific lines.
- **Pydantic validation:** Model responses are accepted only when they satisfy the `ReviewFeedback` schema.
- **Automatic retry:** The service retries once if the generated JSON is invalid.
- **Automatic table creation:** `create_all` simplifies local setup. Production deployments should use Alembic or another migration strategy.

## 🗺️ Roadmap

- [ ] Alembic database migrations
- [ ] Streaming review responses
- [ ] Per-user rate limiting
- [ ] GitHub pull-request integration
- [ ] Review comparison between code versions

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.



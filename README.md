# GitHub Repo Analyzer Backend

A small FastAPI backend that fetches a user's GitHub repositories, stores them in SQLite, and exposes endpoints to query and rank them.

## Features
- Fetch all public repos for a username (handles pagination)
- Store/update repo metadata in repos.db (SQLite)
- Endpoints: /fetch/{username}, /repos, /top
- Authentication via GITHUB_TOKEN loaded from .env (avoids API rate limits)

## Tech Stack
- Python 3.10+
- FastAPI
- SQLite
- Requests
- python-dotenv

## Getting Started

### 1. Clone this repo
```bash
git clone https://github.com/<your-username>/github-repo-analyzer.git
cd github-repo-analyzer
```

### 2. Create a virtual environment
```bash
python -m venv .venv
```

Activate it:

**Windows (PowerShell):**
```powershell
. .venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add environment variable
Create a file called `.env` in the root folder with this line:
```
GITHUB_TOKEN=your_token_here
```

### 5. Run the app
```bash
uvicorn main:app --reload
```

Open Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## API Endpoints
- **GET /fetch/{username}** → Fetches and saves repos for a GitHub user (example: `/fetch/octocat`)
- **GET /repos** → Returns all stored repos (example: `/repos?owner=octocat`)
- **GET /top** → Returns top repos by stars (example: `/top?owner=octocat&limit=5`)

## Notes
- `.env` file should never be pushed to GitHub. (Already added in `.gitignore`)
- `repos.db` (the database file) is local only.

## Example Resume Line
*Developed a FastAPI backend that integrates GitHub API and SQLite to fetch, analyze, and expose repository data via REST endpoints; supports authentication via environment variables.*

## License
MIT License

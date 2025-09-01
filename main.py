import os
import requests
import sqlite3
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DB_NAME = "repos.db"
app = FastAPI(title="GitHub Repo Analyzer Backend")

# ---------- DB SETUP ----------
def get_conn():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS repos (
            repo_id   INTEGER PRIMARY KEY,          -- GitHub repo id (unique)
            name      TEXT        NOT NULL,
            owner     TEXT        NOT NULL,
            stars     INTEGER     NOT NULL,
            forks     INTEGER     NOT NULL,
            language  TEXT,
            html_url  TEXT        NOT NULL,
            updated_at TEXT       NOT NULL
        )
        """
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_repos_owner ON repos(owner)")
    conn.commit()
    conn.close()

init_db()

# Show whether token is loaded
if os.getenv("GITHUB_TOKEN"):
    print("✅ GitHub token detected – using authenticated requests (5000 req/hr).")
else:
    print("⚠️ No GitHub token found – limited to 60 requests/hr.")

# ---------- GITHUB FETCH ----------
def _auth_headers() -> Dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}

def _parse_link_header(link_header: Optional[str]) -> Optional[str]:
    if not link_header:
        return None
    parts = [p.strip() for p in link_header.split(",")]
    for p in parts:
        if 'rel="next"' in p:
            start = p.find("<") + 1
            end = p.find(">")
            return p[start:end]
    return None

def fetch_all_repos(username: str) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/users/{username}/repos"
    params = {"per_page": 100, "sort": "updated", "type": "owner"}
    headers = _auth_headers()

    all_repos: List[Dict[str, Any]] = []
    while url:
        r = requests.get(url, params=params if "per_page" in params else None, headers=headers, timeout=20)
        if r.status_code == 404:
            raise HTTPException(status_code=404, detail="GitHub user not found")
        if r.status_code == 403:
            raise HTTPException(status_code=429, detail="Rate limited by GitHub API. Add a GITHUB_TOKEN in your .env file and try again.")
        r.raise_for_status()

        batch = r.json()
        if isinstance(batch, dict) and "message" in batch:
            raise HTTPException(status_code=400, detail=batch["message"])

        all_repos.extend(batch)
        next_url = _parse_link_header(r.headers.get("Link"))
        url = next_url
        params = {}

    return all_repos

def upsert_repos(repos: List[Dict[str, Any]]) -> int:
    conn = get_conn()
    c = conn.cursor()
    count = 0
    for repo in repos:
        data = (
            repo["id"],
            repo["name"],
            repo["owner"]["login"],
            repo.get("stargazers_count", 0),
            repo.get("forks_count", 0),
            repo.get("language"),
            repo.get("html_url", ""),
            repo.get("updated_at", ""),
        )
        c.execute(
            """
            INSERT INTO repos (repo_id, name, owner, stars, forks, language, html_url, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo_id) DO UPDATE SET
                name=excluded.name,
                owner=excluded.owner,
                stars=excluded.stars,
                forks=excluded.forks,
                language=excluded.language,
                html_url=excluded.html_url,
                updated_at=excluded.updated_at
            """,
            data,
        )
        count += 1
    conn.commit()
    conn.close()
    return count

# ---------- API ENDPOINTS ----------
@app.get("/fetch/{username}")
def fetch_and_store(username: str):
    repos = fetch_all_repos(username)
    saved = upsert_repos(repos)
    return {"status": "ok", "fetched": len(repos), "saved_or_updated": saved, "owner": username}

@app.get("/repos")
def list_repos(owner: Optional[str] = Query(default=None, description="Filter by owner username")):
    conn = get_conn()
    c = conn.cursor()
    if owner:
        c.execute("SELECT name, owner, stars, forks, language, html_url, updated_at FROM repos WHERE owner=? ORDER BY updated_at DESC", (owner,))
    else:
        c.execute("SELECT name, owner, stars, forks, language, html_url, updated_at FROM repos ORDER BY updated_at DESC")
    rows = c.fetchall()
    conn.close()
    keys = ["name", "owner", "stars", "forks", "language", "html_url", "updated_at"]
    return {"count": len(rows), "repos": [dict(zip(keys, r)) for r in rows]}

@app.get("/top")
def top_repos(owner: Optional[str] = Query(default=None), limit: int = Query(default=5, ge=1, le=50)):
    conn = get_conn()
    c = conn.cursor()
    if owner:
        c.execute("SELECT name, owner, stars, forks, language, html_url FROM repos WHERE owner=? ORDER BY stars DESC LIMIT ?", (owner, limit))
    else:
        c.execute("SELECT name, owner, stars, forks, language, html_url FROM repos ORDER BY stars DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    keys = ["name", "owner", "stars", "forks", "language", "html_url"]
    return {"count": len(rows), "top_repos": [dict(zip(keys, r)) for r in rows]}

@app.get("/")
def root():
    return {"message": "Welcome to the GitHub Repo Analyzer API! 🚀",
            "endpoints": ["/fetch/{username}", "/repos", "/top", "/docs"]}

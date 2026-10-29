"""The Price of Everything: isolated Shorts draft queue. No YouTube publishing."""
import os, secrets, sqlite3, datetime
from contextlib import contextmanager
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Price of Everything Shorts Engine", docs_url=None, redoc_url=None)
DB = os.environ.get("SHORTS_DB_PATH", "/tmp/shorts.sqlite3")
TOKEN = os.environ.get("SHORTS_ADMIN_TOKEN", "")

@contextmanager
def database():
    con = sqlite3.connect(DB)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS drafts (id INTEGER PRIMARY KEY, title TEXT NOT NULL, script TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft', created_at TEXT NOT NULL)")
        con.commit()
        yield con
    finally:
        con.close()

def require_admin(authorization: str | None):
    if not TOKEN or not authorization or not secrets.compare_digest(authorization, "Bearer " + TOKEN):
        raise HTTPException(401, "Unauthorized")

class Draft(BaseModel):
    title: str = Field(min_length=4, max_length=120)
    script: str = Field(min_length=30, max_length=5000)

@app.get("/health")
def health():
    return {"status": "ok", "service": "shorts-engine", "youtube_connected": False, "publishing_enabled": False}

@app.post("/api/drafts", status_code=201)
def create_draft(draft: Draft, authorization: str | None = Header(default=None)):
    require_admin(authorization)
    with database() as con:
        cur = con.execute("INSERT INTO drafts (title, script, created_at) VALUES (?, ?, ?)", (draft.title, draft.script, datetime.datetime.now(datetime.timezone.utc).isoformat()))
        con.commit()
        return {"id": cur.lastrowid, "status": "draft"}

@app.get("/api/drafts")
def list_drafts(authorization: str | None = Header(default=None)):
    require_admin(authorization)
    with database() as con:
        return [{"id": i, "title": t, "status": s} for i, t, s in con.execute("SELECT id,title,status FROM drafts ORDER BY id DESC LIMIT 100")]

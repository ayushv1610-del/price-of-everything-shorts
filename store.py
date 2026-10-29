"""Single-replica durable queue, migrations and audit events."""
import os, sqlite3, json, time
from contextlib import contextmanager
from pathlib import Path
DB = os.environ.get('SHORTS_DB_PATH', '/data/shorts.sqlite3')
ROOT = Path(os.environ.get('SHORTS_OUTPUT_DIR', str(Path(DB).parent / 'shorts-output')))
@contextmanager
def database():
    Path(DB).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    try:
        con.execute('PRAGMA journal_mode=WAL')
        con.execute("CREATE TABLE IF NOT EXISTS drafts (id INTEGER PRIMARY KEY, title TEXT NOT NULL, script TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft', created_at TEXT NOT NULL)")
        con.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, key TEXT UNIQUE, plan TEXT NOT NULL, status TEXT NOT NULL, attempts INTEGER DEFAULT 0, error TEXT, created REAL, updated REAL, qa TEXT, approved_hash TEXT, youtube_id TEXT)')
        con.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, job TEXT, action TEXT, detail TEXT, created REAL)')
        con.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
        con.commit()
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
def event(con, job, action, detail=''):
    con.execute('INSERT INTO events(job,action,detail,created) VALUES(?,?,?,?)', (job,action,detail,time.time()))
def setting(key, default=None):
    with database() as c:
        row=c.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
        return json.loads(row[0]) if row else default

def set_setting(key,value):
    with database() as c:
        c.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',(key,json.dumps(value)))

"""SQLite storage for runs and evaluation summaries."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

def now():
    return datetime.now(timezone.utc).isoformat()

class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY, project_path TEXT NOT NULL, question TEXT NOT NULL,
                model TEXT NOT NULL, status TEXT NOT NULL, answer TEXT,
                tool_count INTEGER NOT NULL DEFAULT 0, error TEXT,
                started_at TEXT NOT NULL, finished_at TEXT
            );
            CREATE TABLE IF NOT EXISTS tool_events (
                id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES runs(id),
                tool_name TEXT NOT NULL, status TEXT NOT NULL, duration_ms INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY, run_id INTEGER REFERENCES runs(id), case_id TEXT NOT NULL,
                checks_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_events_run ON tool_events(run_id);
            ''')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.execute('PRAGMA foreign_keys = ON')
        return db

    def start(self, project, question, model):
        with self.connect() as db:
            return db.execute('INSERT INTO runs (project_path, question, model, status, started_at) VALUES (?, ?, ?, ?, ?)', (str(project), question, model, 'running', now())).lastrowid

    def finish(self, run_id, status, answer, count, error=None):
        with self.connect() as db:
            db.execute('UPDATE runs SET status=?, answer=?, tool_count=?, error=?, finished_at=? WHERE id=?', (status, answer, count, error, now(), run_id))

    def event(self, run_id, name, status, duration_ms):
        with self.connect() as db:
            db.execute('INSERT INTO tool_events (run_id, tool_name, status, duration_ms, created_at) VALUES (?, ?, ?, ?, ?)', (run_id, name, status, duration_ms, now()))

    def evaluation(self, run_id, case_id, checks):
        with self.connect() as db:
            db.execute('INSERT INTO evaluations (run_id, case_id, checks_json, created_at) VALUES (?, ?, ?, ?)', (run_id, case_id, json.dumps(checks), now()))

    def history(self, limit=10):
        with self.connect() as db:
            return db.execute('SELECT id, status, model, question, started_at FROM runs ORDER BY id DESC LIMIT ?', (limit,)).fetchall()

    def get_run(self, run_id):
        with self.connect() as db:
            row = db.execute('SELECT id, project_path, question, model, status, answer, tool_count, error, started_at, finished_at FROM runs WHERE id=?', (run_id,)).fetchone()
            events = db.execute('SELECT tool_name, status, duration_ms FROM tool_events WHERE run_id=? ORDER BY id', (run_id,)).fetchall()
        return row, events

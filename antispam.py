import sqlite3
from datetime import datetime, timedelta

DB_PATH = "antispam.db"
WINDOW = timedelta(minutes=30)
MAX_ISSUES = 2

def init():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS issues (user_id INTEGER, ts TEXT)")
    conn.commit()
    conn.close()

def _prune(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cutoff = (datetime.utcnow() - WINDOW).isoformat()
    conn.execute("DELETE FROM issues WHERE user_id=? AND ts<=?", (user_id, cutoff))
    conn.commit()
    conn.close()

def can_issue(user_id: int) -> bool:
    _prune(user_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.execute("SELECT COUNT(*) FROM issues WHERE user_id=?", (user_id,))
    cnt = c.fetchone()[0]
    conn.close()
    return cnt < MAX_ISSUES

def mark_issue(user_id: int):
    _prune(user_id)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO issues (user_id, ts) VALUES (?, ?)", (user_id, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def minutes_left(user_id: int) -> int:
    _prune(user_id)
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT ts FROM issues WHERE user_id=? ORDER BY ts", (user_id,)).fetchall()
    conn.close()
    if len(rows) < MAX_ISSUES:
        return 0
    release_at = datetime.fromisoformat(rows[0][0]) + WINDOW
    left = (release_at - datetime.utcnow()).total_seconds()
    return 0 if left <= 0 else int((left + 59) // 60)
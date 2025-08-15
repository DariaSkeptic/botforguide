import sqlite3
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = "antispam.db"

# Спам-политика
TTL = 30 * 60               # 30 минут окно
DUP_LIMIT = 2               # одинаковую дату >2 раза за TTL — душим
NOISE_LIMIT = 3             # левые сообщения >3 за TTL — душим

def _conn():
    return sqlite3.connect(DB_PATH)

def _init():
    with _conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS date_req (user_id INTEGER, date TEXT, ts INTEGER)")
        c.execute("CREATE TABLE IF NOT EXISTS noise (user_id INTEGER, ts INTEGER, text TEXT)")
        c.commit()

def _prune():
    now = int(time.time())
    with _conn() as c:
        c.execute("DELETE FROM date_req WHERE ts < ?", (now - TTL,))
        c.execute("DELETE FROM noise WHERE ts < ?", (now - TTL,))
        c.commit()

def record_success_date(user_id: int, date_str: str):
    _init(); _prune()
    with _conn() as c:
        c.execute("INSERT INTO date_req (user_id, date, ts) VALUES (?,?,?)", (user_id, date_str, int(time.time())))
        c.commit()

def same_date_too_often(user_id: int, date_str: str) -> bool:
    _init(); _prune()
    with _conn() as c:
        cur = c.execute("SELECT COUNT(*) FROM date_req WHERE user_id=? AND date=?", (user_id, date_str))
        cnt = cur.fetchone()[0]
    return cnt >= DUP_LIMIT

def minutes_left_for_date(user_id: int, date_str: str) -> int:
    _init(); _prune()
    with _conn() as c:
        cur = c.execute("SELECT MIN(ts) FROM date_req WHERE user_id=? AND date=?", (user_id, date_str))
        first = cur.fetchone()[0]
    if not first:
        return 0
    age = int(time.time()) - first
    return max(0, (TTL - age) // 60)

def record_noise(user_id: int, text: str):
    _init(); _prune()
    with _conn() as c:
        c.execute("INSERT INTO noise (user_id, ts, text) VALUES (?,?,?)", (user_id, int(time.time()), text[:100]))
        c.commit()

def noise_too_often(user_id: int) -> bool:
    _init(); _prune()
    with _conn() as c:
        cur = c.execute("SELECT COUNT(*) FROM noise WHERE user_id=?", (user_id,))
        cnt = cur.fetchone()[0]
    return cnt > NOISE_LIMIT

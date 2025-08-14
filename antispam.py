import sqlite3
import time
import logging

logger = logging.getLogger(__name__)

DB_PATH = "antispam.db"
MAX_ISSUES = 2
ISSUE_TTL = 30 * 60  # 30 минут в секундах

def _init_db():
    logger.info("Инициализация базы данных antispam")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS issues (user_id INTEGER, timestamp INTEGER)"
    )
    conn.commit()
    conn.close()

def _prune(user_id: int):
    logger.info(f"Очистка устаревших записей для user_id={user_id}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "DELETE FROM issues WHERE user_id = ? AND timestamp < ?",
        (user_id, int(time.time()) - ISSUE_TTL),
    )
    conn.commit()
    conn.close()

def can_issue(user_id: int) -> bool:
    _init_db()
    _prune(user_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.execute("SELECT COUNT(*) FROM issues WHERE user_id=?", (user_id,))
    cnt = c.fetchone()[0]
    conn.close()
    logger.info(f"Проверка антиспама для user_id={user_id}: count={cnt}, can_issue={cnt < MAX_ISSUES}")
    return cnt < MAX_ISSUES

def mark_issue(user_id: int):
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO issues (user_id, timestamp) VALUES (?, ?)", (user_id, int(time.time())))
    conn.commit()
    conn.close()
    logger.info(f"Записан запрос для user_id={user_id}")

def minutes_left(user_id: int) -> int:
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.execute(
        "SELECT MIN(timestamp) FROM issues WHERE user_id=?", (user_id,)
    )
    ts = c.fetchone()[0]
    conn.close()
    if not ts:
        logger.info(f"Для user_id={user_id} нет записей, minutes_left=0")
        return 0
    age = int(time.time()) - ts
    minutes = max(0, (ISSUE_TTL - age) // 60)
    logger.info(f"Для user_id={user_id} осталось {minutes} минут")
    return minutes
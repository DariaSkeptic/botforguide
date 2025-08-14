import asyncio
import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

def _to_thread(func, *args, **kwargs):
    logger.info(f"Запуск функции {func.__name__} в отдельном потоке")
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, lambda: func(*args, **kwargs))

async def admin_notify(context: ContextTypes.DEFAULT_TYPE, text: str):
    from config import ADMIN_CHAT_ID
    logger.info(f"Отправка уведомления в админ-чат: {text}")
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID не задан")
        return
    try:
        await context.bot.send_message(ADMIN_CHAT_ID, text)
        logger.info("Уведомление успешно отправлено")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {str(e)}")

def fmt_user(user) -> str:
    name = user.first_name or user.username or "Unknown"
    return f"{name} (ID: {user.id})"
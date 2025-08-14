import asyncio
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

def _to_thread(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, lambda: func(*args, **kwargs))

async def admin_notify(context: ContextTypes.DEFAULT_TYPE, text: str):
    from config import ADMIN_CHAT_ID
    if not ADMIN_CHAT_ID:
        return
    try:
        await context.bot.send_message(ADMIN_CHAT_ID, text)
    except Exception:
        pass

def fmt_user(user) -> str:
    name = user.first_name or user.username or "Unknown"
    return f"{name} (ID: {user.id})"
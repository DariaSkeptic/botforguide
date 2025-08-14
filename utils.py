import asyncio
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import ADMIN_CHAT_ID, ADMIN_USER_ID

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

async def _to_thread(func, *args, **kwargs):
    return await asyncio.to_thread(func, *args, **kwargs)

async def admin_notify(context: ContextTypes.DEFAULT_TYPE, text: str):
    if not ADMIN_CHAT_ID:
        return
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, disable_web_page_preview=True)
    except Exception as e:
        logging.warning("Не удалось отправить сообщение в админ-чат: %s", e)

def fmt_user(u) -> str:
    uname = f"@{u.username}" if u and u.username else "—"
    name = f"{u.first_name or ''} {u.last_name or ''}".strip() or "—"
    return f"{name} ({uname}, id={u.id if u else '—'})"

def is_admin(update: Update) -> bool:
    return ADMIN_USER_ID and update.effective_user and update.effective_user.id == ADMIN_USER_ID

def admin_keyboard():
    kb = [
        [InlineKeyboardButton("🧩 Диагностика", callback_data="adm:diag")],
        [InlineKeyboardButton("📁 Недостающие PDF", callback_data="adm:missing")],
        [InlineKeyboardButton("🆔 Мой ID", callback_data="adm:myid"),
         InlineKeyboardButton("📤 Тест в админ-чат", callback_data="adm:test")],
        [InlineKeyboardButton("⚙️ Конфиг", callback_data="adm:cfg")]
    ]
    return InlineKeyboardMarkup(kb)
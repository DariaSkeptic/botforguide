import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ContextTypes, CallbackContext
from gdrive_integration import list_missing_guides, list_existing_guides
from config import ADMIN_USER_ID, ADMIN_CHAT_ID
from utils import admin_notify

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("Недостающие PDF", callback_data="missing_pdfs")],
        [InlineKeyboardButton("Существующие PDF", callback_data="existing_pdfs")],
        [InlineKeyboardButton("Переменные окружения", callback_data="env_vars")],
        [InlineKeyboardButton("ID и настройки", callback_data="ids_settings")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_USER_ID and update.effective_user.id == ADMIN_USER_ID:
        await update.message.reply_text("Админ-панель:", reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text("Доступ запрещён.")

async def admin_panel_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if not (ADMIN_USER_ID and query.from_user.id == ADMIN_USER_ID):
        await query.edit_message_text("Доступ запрещён.")
        return

    if query.data == "missing_pdfs":
        try:
            missing = list_missing_guides()
            text = "Недостающие PDF:\n" + ("\n".join(missing) if missing else "Все на месте.")
        except Exception as e:
            text = f"Ошибка при проверке: {e}"
        await query.edit_message_text(text, reply_markup=get_admin_keyboard())

    elif query.data == "existing_pdfs":
        try:
            existing = list_existing_guides()
            text = "Существующие PDF:\n" + ("\n".join(existing) if existing else "Нет файлов.")
        except Exception as e:
            text = f"Ошибка при проверке: {e}"
        await query.edit_message_text(text, reply_markup=get_admin_keyboard())

    elif query.data == "env_vars":
        env_vars = {
            "BOT_TOKEN": "Задана" if os.getenv("BOT_TOKEN") else "Не задана",
            "ADMIN_USER_ID": os.getenv("ADMIN_USER_ID", "Не задана"),
            "A

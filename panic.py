import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_USER_ID
from utils import admin_notify

logger = logging.getLogger(__name__)

async def cmd_panic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Команда /panic вызвана пользователем {update.effective_user.id}")
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("Эта команда только для админа.")
        logger.warning("Доступ к /panic запрещён")
        return
    await update.message.reply_text("🚨 Паника! Бот в порядке, но ты нажал /panic. Что дальше?")
    await admin_notify(context, f"🚨 Команда /panic вызвана пользователем {update.effective_user.id}")
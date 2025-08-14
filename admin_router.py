import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info(f"Команда /admin вызвана пользователем {user.username} ({user.id})")
    admin_user_id = os.getenv("ADMIN_USER_ID")
    if not admin_user_id:
        logger.error("Переменная ADMIN_USER_ID не задана в окружении!")
        await update.message.reply_text("Ошибка: админ не настроен. Обратитесь к разработчику.")
        return
    try:
        if str(user.id) == admin_user_id:
            keyboard = [
                [InlineKeyboardButton("Недостающие PDF", callback_data="missing_pdfs")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Админ-панель:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Доступ запрещён")
    except Exception as e:
        logger.error(f"Ошибка в cmd_admin: {str(e)}")
        await update.message.reply_text("Ошибка в админ-панели. Обратитесь к разработчику.")

async def admin_panel_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    logger.info(f"Обработка callback от {user.username} ({user.id})")
    admin_user_id = os.getenv("ADMIN_USER_ID")
    if not admin_user_id:
        logger.error("Переменная ADMIN_USER_ID не задана в окружении!")
        await query.edit_message_text("Ошибка: админ не настроен. Обратитесь к разработчику.")
        return
    try:
        if str(user.id) == admin_user_id:
            if query.data == "missing_pdfs":
                from gdrive_integration import list_missing_guides
                missing = list_missing_guides()
                if missing:
                    await query.edit_message_text(f"Недостающие PDF:\n{'\n'.join(missing)}")
                else:
                    await query.edit_message_text("Все PDF на месте!")
        else:
            await query.edit_message_text("Доступ запрещён")
    except Exception as e:
        logger.error(f"Ошибка в admin_panel_callback: {str(e)}")
        await query.edit_message_text("Ошибка при обработке. Обратитесь к разработчику.")
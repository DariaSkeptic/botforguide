from telegram import Update
from telegram.ext import ContextTypes, CallbackContext
import logging
from gdrive_integration import list_missing_guides

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info(f"Команда /admin вызвана пользователем {user.username} ({user.id})")
    if str(user.id) == os.getenv("ADMIN_USER_ID"):
        keyboard = [
            [InlineKeyboardButton("Недостающие PDF", callback_data="missing_pdfs")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Админ-панель:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Доступ запрещён")

async def admin_panel_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    logger.info(f"Обработка callback от {user.username} ({user.id})")
    if str(user.id) == os.getenv("ADMIN_USER_ID"):
        if query.data == "missing_pdfs":
            missing = list_missing_guides()
            if missing:
                await query.edit_message_text(f"Недостающие PDF:\n{'\n'.join(missing)}")
            else:
                await query.edit_message_text("Все PDF на месте!")
    else:
        await query.edit_message_text("Доступ запрещён")
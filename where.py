from telegram import Update
from telegram.ext import ContextTypes

async def cmd_where(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ты находишься в боте для выдачи гайдов по арканам. "
                                    "Используй /start <код> для начала или /admin, если ты администратор.")
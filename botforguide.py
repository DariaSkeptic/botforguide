import os
import re
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from start_router import cmd_start
from admin_router import cmd_admin, admin_panel_callback
from where import cmd_where
from panic import cmd_panic
from antispam import can_issue, mark_issue, minutes_left
from arcana_calc import calc_arcana
from gdrive_service import get_pdf_from_drive

# Настройка логов
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0") or 0)

# вспомогательная отправка дебага админу
async def dbg(context: ContextTypes.DEFAULT_TYPE, text: str):
    logger.debug(text)
    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(ADMIN_CHAT_ID, f"🛠 {text}")
        except Exception:
            pass

# обработчик даты
async def on_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    # проверка формата
    if not re.match(r"^\s*\d{2}\.\d{2}\.\d{4}\s*$", text):
        await update.message.reply_text("Формат даты: ДД.ММ.ГГГГ (например 14.08.1990).")
        return

    program = context.user_data.get("program")
    if not program:
        await update.message.reply_text("Сессия не инициализирована. Перейди по ссылке из Instagram ещё раз.")
        return

    uid = update.effective_user.id
    if not can_issue(uid):
        wait = minutes_left(uid)
        msg = "Лимит выдачи исчерпан. Попробуй позже."
        if wait:
            msg += f" Ориентировочно через {wait} мин."
        await update.message.reply_text(msg)
        return

    try:
        arc = calc_arcana(program, text)
        pretty = {"kapusta": "Капуста", "avatar": "Аватар", "amourchik": "Амурчик"}[program]
        pdf = await get_pdf_from_drive(program, arc)
        await update.message.reply_document(pdf, caption=f"{pretty}: аркан {arc:02d}. Держи свой гайд.")
        mark_issue(uid)
        await dbg(context, f"Выдан гайд {program} аркан {arc:02d} для {uid}")
    except FileNotFoundError:
        await update.message.reply_text("Гайд для этого аркана ещё не добавлен. Напиши админу или попробуй позже.")
        await dbg(context, f"Нет PDF для {program} аркан {arc:02d}")
    except Exception as e:
        logger.exception("Ошибка выдачи PDF")
        await update.message.reply_text("Не получилось выдать файл. Попробуй ещё раз позже.")
        await dbg(context, f"Ошибка выдачи {program}: {e}")

def main():
    logger.info("Запуск бота (botforguide.py)")

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("BOT_TOKEN не задан в переменных окружения.")

    app = Application.builder().token(token).build()

    # регистрируем хендлеры
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.Regex(r"^\s*\d{2}\.\d{2}\.\d{4}\s*$") & filters.TEXT, on_date))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(admin_panel_callback))
    app.add_handler(CommandHandler("where", cmd_where))
    app.add_handler(CommandHandler("panic", cmd_panic))

    logger.info("Запуск polling…")
    app.run_polling(allowed_updates=["message", "callback_query"])
    logger.info("Бот остановлен")

if __name__ == "__main__":
    main()

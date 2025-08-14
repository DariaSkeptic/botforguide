import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# твои хендлеры остаются как есть
from start_router import cmd_start, on_date
from admin_router import cmd_admin, admin_panel_callback
from where import cmd_where
from panic import cmd_panic

# ── ЛОГИ ───────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Запуск бота (botforguide.py)")

    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN не найден в переменных окружения!")
        raise SystemExit("BOT_TOKEN не задан")

    logger.info("Инициализация приложения Telegram…")
    app = Application.builder().token(token).build()

    logger.info("Регистрация обработчиков…")
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.Regex(r"^\s*\d{2}\.\d{2}\.\d{4}\s*$") & filters.TEXT, on_date))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(admin_panel_callback))
    app.add_handler(CommandHandler("where", cmd_where))
    app.add_handler(CommandHandler("panic", cmd_panic))

    logger.info("Запуск polling…")
    # run_polling сам делает initialize/start, снимает вебхук и держит процесс
    app.run_polling(allowed_updates=["message", "callback_query"])
    # сюда выполнение вернётся только при остановке бота
    logger.info("Бот остановлен")

if __name__ == "__main__":
    main()

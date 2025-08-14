import os
import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from start_router import cmd_start, on_date
from admin_router import cmd_admin, admin_panel_callback
from where import cmd_where
from panic import cmd_panic

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def main():
    logger.info("Запуск бота...")
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN не найден в переменных окружения!")
        raise ValueError("BOT_TOKEN не задан")
    
    logger.info("Инициализация приложения Telegram...")
    try:
        app = Application.builder().token(token).build()
    except Exception as e:
        logger.error(f"Ошибка инициализации Telegram: {str(e)}")
        raise
    
    logger.info("Регистрация обработчиков...")
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.Regex(r"^\s*\d{2}\.\d{2}\.\d{4}\s*$") & filters.TEXT, on_date))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(admin_panel_callback))
    app.add_handler(CommandHandler("where", cmd_where))
    app.add_handler(CommandHandler("panic", cmd_panic))
    
    logger.info("Инициализация приложения...")
    await app.initialize()
    logger.info("Запуск polling...")
    try:
        await app.start()
        await app.updater.start_polling(allowed_updates=["message", "callback_query"])
        logger.info("Polling запущен, бот активен")
        # Оставляем приложение работать
        await asyncio.Event().wait()  # Бесконечное ожидание
    except Exception as e:
        logger.error(f"Ошибка в run_polling: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Старт программы botforguide.py")
    try:
        loop = asyncio.get_running_loop()
        logger.info("Используем существующий цикл событий")
    except RuntimeError:
        logger.info("Создаём новый цикл событий")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    logger.info("Добавляем задачу main() в цикл событий")
    loop.create_task(main())
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from start_router import cmd_start, start_go, on_date, on_noise
from admin_router import (
    cmd_missing, cmd_existing, cmd_env, cmd_ids,
    cmd_reset, cmd_restart, set_admin_menu
)
from where import cmd_where
from panic import cmd_panic

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def _post_init(app: Application):
    await set_admin_menu(app)

def main():
    import os
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не задан")

    app = Application.builder().token(token).post_init(_post_init).build()

    # Пользовательский сценарий
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(start_go, pattern=r"^go$"))
    date_regex = r"^\s*\d{2}\.\d{2}\.\d{4}\s*$"
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(date_regex), on_date))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(date_regex), on_noise))

    # Админ-меню (видно только админу — меню команд в строке ввода)
    app.add_handler(CommandHandler("missing", cmd_missing))
    app.add_handler(CommandHandler("existing", cmd_existing))
    app.add_handler(CommandHandler("env", cmd_env))
    app.add_handler(CommandHandler("ids", cmd_ids))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("restart", cmd_restart))

    # Прочее
    app.add_handler(CommandHandler("where", cmd_where))
    app.add_handler(CommandHandler("panic", cmd_panic))

    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()

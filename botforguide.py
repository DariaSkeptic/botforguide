import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from start_router import cmd_start, on_date
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

    # Клиентская логика
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.Regex(r"^\s*\d{2}\.\d{2}\.\d{4}\s*$") & filters.TEXT, on_date))

    # Админ-команды (без /admin панели)
    app.add_handler(CommandHandler("missing", cmd_missing))
    app.add_handler(CommandHandler("existing", cmd_existing))
    app.add_handler(CommandHandler("env", cmd_env))
    app.add_handler(CommandHandler("ids", cmd_ids))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("restart", cmd_restart))

    # Прочее
    app.add_handler(CommandHandler("where", cmd_where))
    app.add_handler(CommandHandler("panic", cmd_panic))

    app.run_polling(allowed_updates=["message"])

if __name__ == "__main__":
    main()

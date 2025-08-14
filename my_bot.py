from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters
)

from config import TOKEN, DATE_REGEX_STR
from antispam import init as antispam_init
from start_router import cmd_start, on_date
from admin_router import cmd_admin, adm_callback, cmd_where, cmd_panic

if __name__ == "__main__":
    antispam_init()
    if not TOKEN:
        raise SystemExit("BOT_TOKEN не задан. Добавь переменную в Railway → Variables.")

    app = ApplicationBuilder().token(TOKEN).build()

    # Клиентские handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.Regex(DATE_REGEX_STR) & filters.TEXT, on_date))

    # Админ handlers
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(adm_callback, pattern=r"^adm:"))
    app.add_handler(CommandHandler("where", cmd_where))
    app.add_handler(CommandHandler("panic", cmd_panic))

    app.run_polling()
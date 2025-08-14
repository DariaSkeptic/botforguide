import os
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from start_router import cmd_start, on_date
from admin_router import cmd_admin, admin_panel_callback
from where import cmd_where
from panic import cmd_panic

async def main():
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.Regex(r"^\s*\d{2}\.\d{2}\.\d{4}\s*$") & filters.TEXT, on_date))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(admin_panel_callback))
    app.add_handler(CommandHandler("where", cmd_where))
    app.add_handler(CommandHandler("panic", cmd_panic))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
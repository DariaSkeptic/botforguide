import os
import logging
from telegram import Update, BotCommand
from telegram.ext import ContextTypes
from gdrive_integration import list_missing_guides, list_existing_guides
from config import ADMIN_USER_ID, ADMIN_CHAT_ID

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def _is_admin(user) -> bool:
    return bool(ADMIN_USER_ID) and (user.id == ADMIN_USER_ID)

async def _deny(update: Update):
    await update.message.reply_text("Access denied.")

async def cmd_missing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user):
        return await _deny(update)
    try:
        items = list_missing_guides()
        text = "Missing PDF:\n" + ("\n".join(items) if items else "All good.")
    except Exception as e:
        text = "Error: " + str(e)
    await update.message.reply_text(text)

async def cmd_existing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user):
        return await _deny(update)
    try:
        items = list_existing_guides()
        text = "Existing PDF:\n" + ("\n".join(items) if items else "No files.")
    except Exception as e:
        text = "Error: " + str(e)
    await update.message.reply_text(text)

async def cmd_env(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user):
        return await _deny(update)
    envs = {
        "BOT_TOKEN": ("set" if os.getenv("BOT_TOKEN") else "unset"),
        "ADMIN_USER_ID": os.getenv("ADMIN_USER_ID", "unset"),
        "ADMIN_CHAT_ID": os.getenv("ADMIN_CHAT_ID", "unset"),
        "GDRIVE_FOLDER_KAPUSTA": os.getenv("GDRIVE_FOLDER_KAPUSTA", "unset"),
        "GDRIVE_FOLDER_AVATAR": os.getenv("GDRIVE_FOLDER_AVATAR", "unset"),
        "GDRIVE_FOLDER_AMOURCHIK": os.getenv("GDRIVE_FOLDER_AMOURCHIK", "unset"),
        "GOOGLE_CREDENTIALS_JSON_B64": ("set" if os.getenv("GOOGLE_CREDENTIALS_JSON_B64") else "unset"),
    }
    lines = [k + ": " + v for k, v in envs.items()]
    await update.message.reply_text("Env:\n" + "\n".join(lines))

async def cmd_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user):
        return await _deny(update)
    txt = (
        "IDs:\n"
        "Your ID: " + str(update.effective_user.id) + "\n"
        "ADMIN_USER_ID: " + str(ADMIN_USER_ID) + "\n"
        "ADMIN_CHAT_ID: " + str(ADMIN_CHAT_ID)
    )
    await update.message.reply_text(txt)

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user):
        return await _deny(update)
    await update.message.reply_text("Bot reset (dummy).")

async def cmd_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user):
        return await _deny(update)
    await update.message.reply_text("Restart requested. Redeploy manually.")

async def set_admin_menu(application):
    """
    Ставим командное меню (без /admin), только полезные пункты.
    Пытаемся ограничить меню админ-чатом, иначе — глобально.
    """
    commands = [
        BotCommand("missing", "Show missing PDFs"),
        BotCommand("existing", "List existing PDFs"),
        BotCommand("env", "Show env vars status"),
        BotCommand("ids", "Show IDs"),
        BotCommand("reset", "Reset bot"),
        BotCommand("restart", "Restart (manual redeploy)"),
    ]

    # Скоп — только админ-чат, если задан
    if ADMIN_CHAT_ID:
        try:
            from telegram import BotCommandScopeChat  # PTB 20+
            scope = BotCommandScopeChat(chat_id=int(ADMIN_CHAT_ID))
            await application.bot.set_my_commands(commands=commands, scope=scope)
            logger.info("Admin menu installed for chat %s", ADMIN_CHAT_ID)
            return
        except Exception as e:
            logger.warning("Scoped admin menu not available (%s). Falling back to global.", e)

    # Фолбэк — глобально
    try:
        await application.bot.set_my_commands(commands=commands)
        logger.info("Global command menu installed as fallback.")
    except Exception as e:
        logger.warning("Failed to set command menu: %s", e)

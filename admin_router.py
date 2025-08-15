import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from gdrive_integration import list_missing_guides, list_existing_guides
from config import ADMIN_USER_ID, ADMIN_CHAT_ID

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def _kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Missing PDF", callback_data="missing_pdfs")],
        [InlineKeyboardButton("Existing PDF", callback_data="existing_pdfs")],
        [InlineKeyboardButton("Env", callback_data="env_vars")],
        [InlineKeyboardButton("IDs", callback_data="ids_settings")],
    ])

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_USER_ID and update.effective_user.id == ADMIN_USER_ID:
        await update.message.reply_text("Admin panel:", reply_markup=_kb())
    else:
        await update.message.reply_text("Access denied.")

async def admin_panel_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if not (ADMIN_USER_ID and query.from_user.id == ADMIN_USER_ID):
        await query.edit_message_text("Access denied.")
        return

    data = query.data
    if data == "missing_pdfs":
        try:
            items = list_missing_guides()
            text = "Missing PDF:\n" + ("\n".join(items) if items else "All good.")
        except Exception as e:
            text = "Error: " + str(e)
        await query.edit_message_text(text, reply_markup=_kb())
        return

    if data == "existing_pdfs":
        try:
            items = list_existing_guides()
            text = "Existing PDF:\n" + ("\n".join(items) if items else "No files.")
        except Exception as e:
            text = "Error: " + str(e)
        await query.edit_message_text(text, reply_markup=_kb())
        return

    if data == "env_vars":
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
        text = "Env:\n" + "\n".join(lines)
        await query.edit_message_text(text, reply_markup=_kb())
        return

    if data == "ids_settings":
        text = "IDs:\nYour ID: " + str(query.from_user.id) + "\nADMIN_USER_ID: " + str(ADMIN_USER_ID) + "\nADMIN_CHAT_ID: " + str(ADMIN_CHAT_ID)
        await query.edit_message_text(text, reply_markup=_kb())
        return

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_USER_ID and update.effective_user.id == ADMIN_USER_ID:
        await update.message.reply_text("Bot reset (dummy).")
    else:
        await update.message.reply_text("Access denied.")

async def cmd_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_USER_ID and update.effective_user.id == ADMIN_USER_ID:
        await update.message.reply_text("Restart requested. Redeploy manually.")
    else:
        await update.message.reply_text("Access denied.")

async def set_admin_menu(application):
    # No-op: keep commands manual to avoid scope issues on PTB 20+
    return

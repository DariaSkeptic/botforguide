import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_USER_ID
from gdrive_integration import list_files_in_folder
from utils import admin_notify

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("Эта команда только для админа.")
        return
    keyboard = [
        [InlineKeyboardButton("Диагностика", callback_data="diag")],
        [InlineKeyboardButton("Недостающие PDF", callback_data="missing_pdf")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Панель админа:", reply_markup=reply_markup)

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_USER_ID:
        await query.answer("Эта кнопка только для админа.")
        return
    await query.answer()
    from config import GDRIVE_FOLDERS
    if query.data == "diag":
        ok = []
        missing = []
        for prog, folder_id in GDRIVE_FOLDERS.items():
            files = await list_files_in_folder(folder_id or "")
            if files is None or folder_id is None:
                missing.append(prog)
            else:
                ok.append(prog)
        msg = "Диагностика Google Drive:\n"
        msg += f"OK: {', '.join(ok) or 'нет'}\n" if ok else ""
        msg += f"Ошибка: {', '.join(missing) or 'нет'}\n" if missing else ""
        await query.message.reply_text(msg)
        await admin_notify(context, f"🛠 Диагностика\n{msg}")
    elif query.data == "missing_pdf":
        msg = "Недостающие PDF:\n"
        for prog, folder_id in GDRIVE_FOLDERS.items():
            if not folder_id:
                msg += f"{prog}: папка не настроена\n"
                continue
            files = await list_files_in_folder(folder_id)
            if files is None:
                msg += f"{prog}: ошибка доступа к папке\n"
                continue
            found = {f["name"] for f in files}
            missing = [f"{n:02d}.pdf" for n in range(1, 23) if f"{n:02d}.pdf" not in found]
            msg += f"{prog}: {', '.join(missing) or 'все файлы на месте'}\n"
        await query.message.reply_text(msg)
        await admin_notify(context, f"🛠 Недостающие PDF\n{msg}")
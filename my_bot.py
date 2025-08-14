import os
import re
import json
import base64
import sqlite3
import logging
from io import BytesIO
from datetime import datetime, timedelta
from typing import Optional

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)

# ---------------------- ЛОГИ ----------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# ---------------------- КОНФИГ ----------------------
TOKEN = os.environ["BOT_TOKEN"]

# папки на Google Drive
GDRIVE_FOLDER_KAPUSTA = os.environ["GDRIVE_FOLDER_KAPUSTA"]
GDRIVE_FOLDER_AVATAR = os.environ["GDRIVE_FOLDER_AVATAR"]
GDRIVE_FOLDER_AMOURCHIK = os.environ["GDRIVE_FOLDER_AMOURCHIK"]

# креды сервис-аккаунта (Base64 от credentials.json)
GOOGLE_CREDENTIALS_JSON_B64 = os.environ["GOOGLE_CREDENTIALS_JSON_B64"]

PROGRAM_FOLDERS = {
    "kapusta": GDRIVE_FOLDER_KAPUSTA,
    "avatar": GDRIVE_FOLDER_AVATAR,
    "amourchik": GDRIVE_FOLDER_AMOURCHIK,
}

CODEWORDS = {
    "капуста": "kapusta",
    "kapusta": "kapusta",
    "аватар": "avatar",
    "avatar": "avatar",
    "амурчик": "amourchik",
    "amourchik": "amourchik",
    "amour": "amourchik",
}

DATE_RE = re.compile(r"^\s*(\d{2})\.(\d{2})\.(\d{4})\s*$")

# ---------------------- АНТИСПАМ ----------------------
DB_PATH = "antispam.db"
WINDOW = timedelta(minutes=30)
MAX_ISSUES = 2

def antispam_init():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS issues (user_id INTEGER, ts TEXT)")
    conn.commit()
    conn.close()

def _prune(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cutoff = (datetime.utcnow() - WINDOW).isoformat()
    conn.execute("DELETE FROM issues WHERE user_id=? AND ts<=?", (user_id, cutoff))
    conn.commit()
    conn.close()

def can_issue(user_id: int) -> bool:
    _prune(user_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.execute("SELECT COUNT(*) FROM issues WHERE user_id=?", (user_id,))
    cnt = c.fetchone()[0]
    conn.close()
    return cnt < MAX_ISSUES

def mark_issue(user_id: int):
    _prune(user_id)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO issues (user_id, ts) VALUES (?, ?)", (user_id, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def minutes_left(user_id: int) -> int:
    _prune(user_id)
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT ts FROM issues WHERE user_id=? ORDER BY ts", (user_id,)).fetchall()
    conn.close()
    if len(rows) < MAX_ISSUES:
        return 0
    release_at = datetime.fromisoformat(rows[0][0]) + WINDOW
    left = (release_at - datetime.utcnow()).total_seconds()
    return 0 if left <= 0 else int((left + 59) // 60)

# ---------------------- REDUCTION / МАТЕМАТИКА ----------------------
def reduce_arcana(n: int) -> int:
    n = abs(int(n))
    while n > 22:
        n = sum(int(d) for d in str(n))
        if n == 0:
            n = 22
    if n < 1:
        n = 1
    return n

def compute_points(date_str: str) -> dict:
    dt = datetime.strptime(date_str, "%d.%m.%Y")
    day, month, year = dt.day, dt.month, dt.year
    A = reduce_arcana(sum(int(d) for d in f"{day:02d}"))
    B = reduce_arcana(sum(int(d) for d in f"{month:02d}"))
    V = reduce_arcana(sum(int(d) for d in f"{year:04d}"))
    G = reduce_arcana(A + B + V)            # деньги
    D = reduce_arcana(A + B + V + G)        # восприятие
    E = reduce_arcana(D + G)                # любовь
    return {"A": A, "B": B, "V": V, "G": G, "D": D, "E": E}

def calc_arcana(program: str, date_str: str) -> int:
    pts = compute_points(date_str)
    if program == "kapusta":
        return pts["G"]
    if program == "avatar":
        return pts["D"]
    return pts["E"]  # amourchik

# ---------------------- GOOGLE DRIVE ----------------------
def _gclient():
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    info = json.loads(base64.b64decode(GOOGLE_CREDENTIALS_JSON_B64))
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/drive.readonly"])
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def gdrive_find_file_id(folder_id: str, filename: str) -> Optional[str]:
    svc = _gclient()
    q = f"'{folder_id}' in parents and name = '{filename}' and trashed = false"
    res = svc.files().list(q=q, fields="files(id,name)", pageSize=1).execute()
    files = res.get("files", [])
    return files[0]["id"] if files else None

def gdrive_download_bytes(file_id: str) -> bytes:
    from googleapiclient.http import MediaIoBaseDownload
    svc = _gclient()
    req = svc.files().get_media(fileId=file_id)
    buf = BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    buf.seek(0)
    return buf.read()

async def get_pdf_from_drive(program: str, arcana: int) -> InputFile:
    folder = PROGRAM_FOLDERS[program]
    filename = f"{arcana:02}.pdf"
    file_id = await _to_thread(gdrive_find_file_id, folder, filename)
    if not file_id:
        raise FileNotFoundError(f"Нет {filename} в папке {program}")
    data = await _to_thread(gdrive_download_bytes, file_id)
    return InputFile(BytesIO(data), filename=filename)

# ---------------------- ХЕЛПЕРЫ ----------------------
def start_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("СТАРТ", callback_data="go")]])

async def _to_thread(func, *args, **kwargs):
    import asyncio
    return await asyncio.to_thread(func, *args, **kwargs)

def _extract_program_from_args(context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    if not getattr(context, "args", None):
        return None
    if not context.args:
        return None
    raw = context.args[0].strip().lower()
    return CODEWORDS.get(raw)

def _extract_program_from_text(text: str) -> Optional[str]:
    return CODEWORDS.get(text.strip().lower())

# ---------------------- ХЕНДЛЕРЫ ----------------------
ASK_DATE = 1  # состояние диалога

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /start [codeword] — программа задаётся кодовым словом из Инсты.
        Никакого выбора. Сразу выдаём кнопку СТАРТ (текст согласий у тебя в Description).
    """
    # 1) фиксируем программу
    program = _extract_program_from_args(context)
    if program:
        context.user_data["program"] = program

    # 2) если программы нет — просим кодовое слово
    if not context.user_data.get("program"):
        await (update.message or update.callback_query.message).reply_text(
            "Введи кодовое слово: капуста / аватар / амурчик"
        )
        return ConversationHandler.END

    # 3) показываем кнопку СТАРТ
    if update.message:
        await update.message.reply_text("Нажми «СТАРТ», чтобы начать.", reply_markup=start_keyboard())
    else:
        await update.callback_query.message.reply_text("Нажми «СТАРТ», чтобы начать.", reply_markup=start_keyboard())
    return ConversationHandler.END

async def on_codeword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("program"):
        return  # уже есть
    program = _extract_program_from_text(update.message.text)
    if not program:
        return
    context.user_data["program"] = program
    await update.message.reply_text("Нажми «СТАРТ», чтобы начать.", reply_markup=start_keyboard())

async def on_go(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user = update.effective_user
    name = user.first_name or user.username or "друг"
    # Приветствие — без упоминаний согласий
    await update.callback_query.message.reply_text(
        f"Привет, {name}. Кидай дату рождения в формате ДД.ММ.ГГГГ."
    )
    return ASK_DATE

async def on_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not DATE_RE.match(text):
        await update.message.reply_text("Формат даты: ДД.ММ.ГГГГ (например 14.08.1990).")
        return ASK_DATE

    program = context.user_data.get("program")
    if not program:
        await update.message.reply_text("Сначала введи кодовое слово: капуста / аватар / амурчик.")
        return ConversationHandler.END

    uid = update.effective_user.id
    if not can_issue(uid):
        wait = minutes_left(uid)
        msg = "Лимит выдачи исчерпан. Попробуй позже."
        if wait:
            msg += f" Ориентировочно через {wait} мин."
        await update.message.reply_text(msg)
        return ConversationHandler.END

    try:
        arc = calc_arcana(program, text)
        pdf = await get_pdf_from_drive(program, arc)
        pretty = {"kapusta": "Капуста", "avatar": "Аватар", "amourchik": "Амурчик"}[program]
        await update.message.reply_document(
            pdf,
            caption=f"{pretty}: аркан {arc:02d}. Держи свой гайд."
        )
        mark_issue(uid)
    except FileNotFoundError:
        await update.message.reply_text("Гайд не найден. Сообщи администратору, чтобы докинуть PDF.")
    except Exception as e:
        logging.exception("Ошибка выдачи PDF: %s", e)
        await update.message.reply_text("Не получилось выдать файл. Попробуй ещё раз позже.")

    # Диалог завершаем. Для нового расчёта — снова кодовое слово или ссылка из Инсты.
    return ConversationHandler.END

# ---------------------- MAIN ----------------------
if __name__ == "__main__":
    antispam_init()

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(on_go, pattern="^go$"),
        ],
        states={
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_date)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_codeword))
    app.add_handler(conv)

    app.run_polling()

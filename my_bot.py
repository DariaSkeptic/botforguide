# my_bot.py
# python-telegram-bot==20.3
import os
import re
import json
import base64
import sqlite3
import logging
from io import BytesIO
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)

# ────────────────────────── ЛОГИ ──────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# ────────────────────────── КОНФИГ ────────────────────────
# ОБЯЗАТЕЛЬНО задать эти переменные на Railway:
# BOT_TOKEN, ADMIN_CHAT_ID, (опц) ADMIN_USER_ID,
# GOOGLE_CREDENTIALS_JSON_B64, GDRIVE_FOLDER_KAPUSTA/AVATAR/AMOURCHIK
TOKEN = os.environ.get("BOT_TOKEN", "").strip()
GDRIVE_FOLDER_KAPUSTA   = os.environ.get("GDRIVE_FOLDER_KAPUSTA", "").strip()
GDRIVE_FOLDER_AVATAR    = os.environ.get("GDRIVE_FOLDER_AVATAR", "").strip()
GDRIVE_FOLDER_AMOURCHIK = os.environ.get("GDRIVE_FOLDER_AMOURCHIK", "").strip()
GOOGLE_CREDENTIALS_JSON_B64 = os.environ.get("GOOGLE_CREDENTIALS_JSON_B64", "").strip()

PROGRAM_FOLDERS: Dict[str, str] = {
    "kapusta":   GDRIVE_FOLDER_KAPUSTA,
    "avatar":    GDRIVE_FOLDER_AVATAR,
    "amourchik": GDRIVE_FOLDER_AMOURCHIK,
}

ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "0") or "0")
ADMIN_USER_ID = int(os.environ.get("ADMIN_USER_ID", "0") or "0")

# Кодовые слова (из Инсты / вручную)
CODEWORDS = {
    "капуста": "kapusta", "kapusta": "kapusta",
    "аватар": "avatar",   "avatar":  "avatar",
    "амурчик": "amourchik", "amourchik": "amourchik", "amour": "amourchik",
}

DATE_RE = re.compile(r"^\s*(\d{2})\.(\d{2})\.(\d{4})\s*$")

# ─────────────────────── АНТИСПАМ (sqlite) ───────────────────────
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

# ─────────────── РЕДУКЦИЯ и ТОЧКИ Г/Д/Е ───────────────
def reduce_arcana(n: int) -> int:
    n = abs(int(n))
    while n > 22:
        n = sum(int(d) for d in str(n))
        if n == 0:
            n = 22
    return 1 if n < 1 else n

def compute_points(date_str: str) -> dict:
    # Базовый расчёт: A,B,V по сумме цифр дня/месяца/года; редукция до 1–22
    dt = datetime.strptime(date_str, "%d.%m.%Y")
    day, month, year = dt.day, dt.month, dt.year
    A = reduce_arcana(sum(int(d) for d in f"{day:02d}"))
    B = reduce_arcana(sum(int(d) for d in f"{month:02d}"))
    V = reduce_arcana(sum(int(d) for d in f"{year:04d}"))
    G = reduce_arcana(A + B + V)        # деньги
    D = reduce_arcana(A + B + V + G)    # восприятие
    E = reduce_arcana(D + G)            # любовь
    return {"A": A, "B": B, "V": V, "G": G, "D": D, "E": E}

def calc_arcana(program: str, date_str: str) -> int:
    pts = compute_points(date_str)
    if program == "kapusta":
        return pts["G"]
    if program == "avatar":
        return pts["D"]
    return pts["E"]  # amourchik

# ───────────────────── Google Drive ─────────────────────
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

def gdrive_list_filenames(folder_id: str) -> List[str]:
    svc = _gclient()
    files: List[str] = []
    page_token = None
    while True:
        res = svc.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="nextPageToken, files(name)",
            pageSize=1000,
            pageToken=page_token
        ).execute()
        files.extend([f["name"] for f in res.get("files", []) if "name" in f])
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return files

async def get_pdf_from_drive(program: str, arcana: int) -> InputFile:
    filename = f"{arcana:02}.pdf"
    folder_id = PROGRAM_FOLDERS[program]
    file_id = await _to_thread(gdrive_find_file_id, folder_id, filename)
    if not file_id:
        raise FileNotFoundError(f"Нет {filename} в папке {program}")
    data = await _to_thread(gdrive_download_bytes, file_id)
    return InputFile(BytesIO(data), filename=filename)

# ───────────────────── Хелперы ─────────────────────
def start_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("СТАРТ", callback_data="go")]])

def admin_keyboard():
    kb = [
        [InlineKeyboardButton("🧩 Диагностика", callback_data="adm:diag")],
        [InlineKeyboardButton("📁 Недостающие PDF", callback_data="adm:missing")],
        [InlineKeyboardButton("🆔 Мой ID", callback_data="adm:myid"),
         InlineKeyboardButton("📤 Тест в админ-чат", callback_data="adm:test")],
        [InlineKeyboardButton("⚙️ Конфиг", callback_data="adm:cfg")]
    ]
    return InlineKeyboardMarkup(kb)

async def _to_thread(func, *args, **kwargs):
    import asyncio
    return await asyncio.to_thread(func, *args, **kwargs)

def _extract_program_from_args(context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    if not getattr(context, "args", None): return None
    if not context.args: return None
    raw = context.args[0].strip().lower()
    return CODEWORDS.get(raw)

def _extract_program_from_text(text: str) -> Optional[str]:
    return CODEWORDS.get(text.strip().lower())

async def admin_notify(context: ContextTypes.DEFAULT_TYPE, text: str):
    if not ADMIN_CHAT_ID:
        return
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, disable_web_page_preview=True)
    except Exception as e:
        logging.warning("Не удалось отправить уведомление админу: %s", e)

def fmt_user(u) -> str:
    uname = f"@{u.username}" if u and u.username else "—"
    name = f"{u.first_name or ''} {u.last_name or ''}".strip() or "—"
    return f"{name} ({uname}, id={u.id if u else '—'})"

def _is_admin(update: Update) -> bool:
    return ADMIN_USER_ID and update.effective_user and update.effective_user.id == ADMIN_USER_ID

# ───────────────────── Состояния ─────────────────────
ASK_DATE = 1  # ждём дату

# ───────────────────── Клиентский поток ─────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start [codeword] — программа задаётся кодовым словом.
    В боте: показываем только кнопку «СТАРТ». Юрдоки/согласия — в твоём Description перед кнопкой.
    """
    program = _extract_program_from_args(context)
    if program:
        context.user_data["program"] = program

    if not context.user_data.get("program"):
        target = update.message or update.callback_query.message
        await target.reply_text("Введи кодовое слово: капуста / аватар / амурчик")
        return ConversationHandler.END

    target = update.message or update.callback_query.message
    await target.reply_text("Нажми «СТАРТ», чтобы начать.", reply_markup=start_keyboard())

    u = update.effective_user
    prog = context.user_data.get("program", "—")
    await admin_notify(context, f"🟡 Старт сценария\nПрограмма: {prog}\nПользователь: {fmt_user(u)}")

    return ConversationHandler.END

async def on_codeword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("program"):
        return
    program = _extract_program_from_text(update.message.text)
    if not program:
        return
    context.user_data["program"] = program
    await update.message.reply_text("Нажми «СТАРТ», чтобы начать.", reply_markup=start_keyboard())
    await admin_notify(context, f"🟡 Получено кодовое слово\nПрограмма: {program}\nПользователь: {fmt_user(update.effective_user)}")

async def on_go(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user = update.effective_user
    name = user.first_name or user.username or "друг"
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
        await admin_notify(context, f"⛔️ Антиспам\nПользователь: {fmt_user(update.effective_user)}\n"
                                    f"Программа: {program}\nДата: {text}\nОсталось: ~{wait} мин")
        msg = "Лимит выдачи исчерпан. Попробуй позже."
        if wait: msg += f" Ориентировочно через {wait} мин."
        await update.message.reply_text(msg)
        return ConversationHandler.END

    try:
        arc = calc_arcana(program, text)
        pdf = await get_pdf_from_drive(program, arc)
        pretty = {"kapusta": "Капуста", "avatar": "Аватар", "amourchik": "Амурчик"}[program]
        await update.message.reply_document(pdf, caption=f"{pretty}: аркан {arc:02d}. Держи свой гайд.")
        mark_issue(uid)
        await admin_notify(context, f"✅ Выдан гайд\nПрограмма: {program} | Аркан: {arc:02d}\n"
                                    f"Дата клиента: {text}\nПользователь: {fmt_user(update.effective_user)}")
    except FileNotFoundError:
        await update.message.reply_text(
            "Гайд для этого аркана ещё не добавлен. Напиши админу или попробуй позже."
        )
        await admin_notify(context, f"❗️ Гайд отсутствует на диске\nПрограмма: {program}\nДата клиента: {text}\n"
                                    f"Ожидался файл: {arc:02d}.pdf")
    except Exception as e:
        logging.exception("Ошибка выдачи PDF: %s", e)
        await update.message.reply_text("Не получилось выдать файл. Попробуй ещё раз позже.")
        await admin_notify(context, f"🔥 Ошибка выдачи\nПрограмма: {program}\nДата клиента: {text}\nОшибка: {e}")

    return ConversationHandler.END

# ───────────────────── Админ‑панель ─────────────────────
async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update): return
    await update.message.reply_text("Панель администратора:", reply_markup=admin_keyboard())

async def adm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update): 
        await update.callback_query.answer()
        return
    data = update.callback_query.data
    await update.callback_query.answer()

    if data == "adm:diag":
        await admin_diag(update, context)
    elif data == "adm:missing":
        await admin_missing(update, context)
    elif data == "adm:myid":
        await update.callback_query.message.reply_text(f"Твой Telegram ID: <code>{update.effective_user.id}</code>", parse_mode="HTML")
    elif data == "adm:test":
        await admin_notify(context, "Тест: сообщение в админ‑чат работает ✅")
        await update.callback_query.message.reply_text("Отправила тест в админ‑чат.")
    elif data == "adm:cfg":
        await admin_cfg(update, context)

async def admin_diag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем базовые вещи: токен, креды, папки
    problems = []
    ok = []
    if TOKEN: ok.append("BOT_TOKEN: OK")
    else: problems.append("BOT_TOKEN: НЕ задан")

    if GOOGLE_CREDENTIALS_JSON_B64:
        try:
            json.loads(base64.b64decode(GOOGLE_CREDENTIALS_JSON_B64))
            ok.append("GOOGLE_CREDENTIALS_JSON_B64: OK")
        except Exception:
            problems.append("GOOGLE_CREDENTIALS_JSON_B64: НЕ декодируется")
    else:
        problems.append("GOOGLE_CREDENTIALS_JSON_B64: НЕ задан")

    for k, v in PROGRAM_FOLDERS.items():
        if v: ok.append(f"GDRIVE_FOLDER_{k.upper()}: OK")
        else: problems.append(f"GDRIVE_FOLDER_{k.upper()}: НЕ задан")

    if ADMIN_CHAT_ID: ok.append(f"ADMIN_CHAT_ID: OK ({ADMIN_CHAT_ID})")
    else: problems.append("ADMIN_CHAT_ID: НЕ задан")

    if ADMIN_USER_ID: ok.append(f"ADMIN_USER_ID: OK ({ADMIN_USER_ID})")
    else: ok.append("ADMIN_USER_ID: не задан (необязательно)")

    text = "🧩 Диагностика\n\n"
    if ok: text += "✅ OK:\n- " + "\n- ".join(ok) + "\n\n"
    if problems: text += "❌ Проблемы:\n- " + "\n- ".join(problems)
    else: text += "Проблем не вижу."

    await update.callback_query.message.reply_text(text)

async def admin_missing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Для каждой программы проверяем, какие NN.pdf отсутствуют (01..22)
    report_lines = ["📁 Недостающие PDF:"]
    try:
        for program, folder in PROGRAM_FOLDERS.items():
            if not folder:
                report_lines.append(f"- {program}: папка не настроена")
                continue
            try:
                names = await _to_thread(gdrive_list_filenames, folder)
                have = {n.lower() for n in names}
                required = [f"{i:02}.pdf" for i in range(1, 23)]
                missing = [f for f in required if f.lower() not in have]
                if missing:
                    report_lines.append(f"- {program}: нет {', '.join(missing)}")
                else:
                    report_lines.append(f"- {program}: все 22 файла на месте ✅")
            except Exception as e:
                report_lines.append(f"- {program}: ошибка доступа к папке ({e})")
    except Exception as e:
        report_lines.append(f"Общая ошибка: {e}")

    await update.callback_query.message.reply_text("\n".join(report_lines))

async def admin_cfg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Показать конфиг (без секретов)
    pretty_map = {
        "kapusta": GDRIVE_FOLDER_KAPUSTA,
        "avatar": GDRIVE_FOLDER_AVATAR,
        "amourchik": GDRIVE_FOLDER_AMOURCHIK,
    }
    text = (
        "⚙️ Конфиг (без секретов):\n"
        f"- ADMIN_CHAT_ID: {ADMIN_CHAT_ID or '—'}\n"
        f"- ADMIN_USER_ID: {ADMIN_USER_ID or '—'}\n"
        f"- Folders:\n"
        f"  • kapusta:   {'настроена' if pretty_map['kapusta'] else '—'}\n"
        f"  • avatar:    {'настроена' if pretty_map['avatar'] else '—'}\n"
        f"  • amourchik: {'настроена' if pretty_map['amourchik'] else '—'}\n"
        "- Диапазон арканов: 01..22\n"
        "- Антиспам: 2 выдачи / 30 мин"
    )
    await update.callback_query.message.reply_text(text)

# ───────────── Сервисные команды (как в «боте для ботов») ─────────────
async def cmd_where(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update): return
    c = update.effective_chat
    await update.message.reply_text(
        f"chat.id = <code>{c.id}</code>\n"
        f"type = <b>{c.type}</b>\n"
        f"title = {c.title or '—'}",
        parse_mode="HTML"
    )

async def cmd_panic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update): return
    args = (update.message.text or "").split()
    if len(args) < 2:
        await update.message.reply_text("Укажи chat_id: /panic -1001234567890")
        return
    try:
        chat_id = int(args[1])
        await context.bot.leave_chat(chat_id)
        await update.message.reply_text(f"Вышла из чата {chat_id}")
    except Exception as e:
        await update.message.reply_text(f"Не смогла: {e}")

# ────────────────────────── MAIN ──────────────────────────
if __name__ == "__main__":
    antispam_init()

    if not TOKEN:
        raise SystemExit("BOT_TOKEN не задан. Добавь переменную в Railway → Variables.")

    app = ApplicationBuilder().token(TOKEN).build()

    # Клиентский поток
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_go, pattern="^go$")],
        states={ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_date)]},
        fallbacks=[]
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_codeword))  # кодовое слово

    # Админ‑панель
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(adm_callback, pattern=r"^adm:"))
    app.add_handler(CommandHandler("where", cmd_where))
    app.add_handler(CommandHandler("panic", cmd_panic))

    app.run_polling()

from telegram import Update
from telegram.ext import ContextTypes

from config import TOKEN, GOOGLE_CREDENTIALS_JSON_B64, PROGRAM_FOLDERS, ADMIN_CHAT_ID, ADMIN_USER_ID
from utils import admin_keyboard, admin_notify, is_admin, _to_thread
from gdrive_integration import list_filenames
import base64
import json
import logging

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    await update.message.reply_text("Панель администратора:", reply_markup=admin_keyboard())

async def adm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.callback_query.answer()
        return
    data = update.callback_query.data
    await update.callback_query.answer()
    if data == "adm:diag":
        await admin_diag(update, context)
    elif data == "adm:missing":
        await admin_missing(update, context)
    elif data == "adm:myid":
        await update.callback_query.message.reply_text(
            f"Твой Telegram ID: <code>{update.effective_user.id}</code>", parse_mode="HTML"
        )
    elif data == "adm:test":
        await admin_notify(context, "Тест: сообщение в админ‑чат работает ✅")
        await update.callback_query.message.reply_text("Отправила тест в админ‑чат.")
    elif data == "adm:cfg":
        await admin_cfg(update, context)

async def admin_diag(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    report_lines = ["📁 Недостающие PDF:"]
    try:
        for program, folder in PROGRAM_FOLDERS.items():
            if not folder:
                report_lines.append(f"- {program}: папка не настроена")
                continue
            try:
                names = await _to_thread(list_filenames, folder)
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
    pretty_map = {
        "kapusta": PROGRAM_FOLDERS["kapusta"],
        "avatar": PROGRAM_FOLDERS["avatar"],
        "amourchik": PROGRAM_FOLDERS["amourchik"],
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

async def cmd_where(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    c = update.effective_chat
    await update.message.reply_text(
        f"chat.id = <code>{c.id}</code>\n"
        f"type = <b>{c.type}</b>\n"
        f"title = {c.title or '—'}",
        parse_mode="HTML"
    )

async def cmd_panic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
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
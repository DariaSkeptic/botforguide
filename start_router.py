import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import CODEWORDS, DATE_RE
from utils import admin_notify, fmt_user
from arcana_calculator import calc_arcana
from gdrive_integration import get_pdf
from antispam import can_issue, mark_issue, minutes_left

def _extract_program_from_args(context: ContextTypes.DEFAULT_TYPE) -> str | None:
    if not getattr(context, "args", None): return None
    if not context.args: return None
    raw = context.args[0].strip().lower()
    return CODEWORDS.get(raw)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    program = _extract_program_from_args(context)
    if not program:
        target = update.message or update.callback_query.message
        await target.reply_text(
            "Некорректная или устаревшая ссылка запуска. Перейди по актуальной ссылке из Instagram."
        )
        return
    context.user_data["program"] = program
    user = update.effective_user
    name = user.first_name or user.username or "друг"
    await (update.message or update.callback_query.message).reply_text(
        f"Привет, {name}. Кидай дату рождения в формате ДД.ММ.ГГГГ."
    )
    await admin_notify(context, f"🟡 Старт сценария\nПрограмма: {program}\nПользователь: {fmt_user(user)}")

async def on_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    await update.message.reply_text(f"DEBUG: Получен текст: '{text}'")
    if not DATE_RE.match(text):
        await update.message.reply_text("Формат даты: ДД.ММ.ГГГГ (например 14.08.1990).")
        await update.message.reply_text(f"DEBUG: Regex не пройден для '{text}'")
        return
    await update.message.reply_text(f"DEBUG: Regex пройден, текст: '{text}'")
    program = context.user_data.get("program")
    if not program:
        await update.message.reply_text(
            "Сессия не инициализирована. Перейди по ссылке из Instagram ещё раз."
        )
        await update.message.reply_text(f"DEBUG: Нет программы в user_data")
        return
    await update.message.reply_text(f"DEBUG: Программа: {program}")
    uid = update.effective_user.id
    await update.message.reply_text(f"DEBUG: Антиспам can_issue={can_issue(uid)}")
    if not can_issue(uid):
        wait = minutes_left(uid)
        await admin_notify(context, f"⛔️ Антиспам\nПользователь: {fmt_user(update.effective_user)}\n"
                                    f"Программа: {program}\nДата: {text}\nОсталось: ~{wait} мин")
        msg = "Лимит выдачи исчерпан. Попробуй позже."
        if wait: msg += f" Ориентировочно через {wait} мин."
        await update.message.reply_text(msg)
        await update.message.reply_text(f"DEBUG: Антиспам заблокировал")
        return
    try:
        arc = calc_arcana(program, text)
        await update.message.reply_text(f"DEBUG: Аркан вычислен: {arc}")
        pdf = await get_pdf(program, arc)
        await update.message.reply_text(f"DEBUG: PDF загружен для {program}, аркан {arc}")
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
        await update.message.reply_text(f"DEBUG: FileNotFoundError для {arc:02d}.pdf")
    except Exception as e:
        logging.exception("Ошибка выдачи PDF: %s", e)
        await update.message.reply_text("Не получилось выдать файл. Попробуй ещё раз позже.")
        await admin_notify(context, f"🔥 Ошибка выдачи\nПрограмма: {program}\nДата клиента: {text}\nОшибка: {e}")
        await update.message.reply_text(f"DEBUG: Ошибка: {str(e)}")
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import CODEWORDS, DATE_RE, ADMIN_CHAT_ID
from arcana_calculator import calculate_arcana
from antispam import same_date_too_often, minutes_left_for_date, record_success_date, record_noise, noise_too_often
from gdrive_integration import get_guide
from utils import admin_notify, fmt_user

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# поддерживаем рус/лат алиасы, но клиент НИЧЕГО не выбирает
ALIAS = {
    "капуста": "kapusta", "kapusta": "kapusta",
    "аватар": "avatar",  "avatar":  "avatar",
    "амурчик": "amourchik", "amurchik": "amourchik", "amourchik": "amourchik",
}

DEFAULT_PROGRAM = os.getenv("DEFAULT_PROGRAM", "kapusta")  # можно поменять без кода

def _program_from_args(args) -> str:
    if not args:
        return DEFAULT_PROGRAM
    key = (args[0] or "").strip().lower()
    return ALIAS.get(key, DEFAULT_PROGRAM)

def _start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("СТАРТ", callback_data="go")]])

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Только кнопка СТАРТ. Никаких кодов, подсказок и т.п."""
    program = _program_from_args(context.args)
    context.user_data["program"] = program
    await update.message.reply_text(" ", reply_markup=_start_keyboard())

    # логи по /start не шлём — нужны только по факту выдачи/ошибки

async def start_go(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """После нажатия — приветствие + инструкция. Направление уже выбрано из инсты."""
    q = update.callback_query
    await q.answer()
    greeting = (
        "Привет! Работаем быстро и по делу.\n\n"
        "Отправь дату рождения в формате ДД.ММ.ГГГГ\n"
        "пример: 01.06.1926\n\n"
        "Выдам один PDF. Без спама, без лишних сообщений."
    )
    await q.message.reply_text(greeting)

async def on_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем дату → считаем нужную точку (Г/Д/Е) → шлём ОДИН PDF."""
    user = update.effective_user
    text = (update.message.text or "").strip()

    # формат
    if not DATE_RE.match(text):
        await update.message.reply_text("Формат даты: ДД.ММ.ГГГГ. Пример: 01.06.1926")
        return

    # защитимся от тупого повторения одной и той же даты
    if same_date_too_often(user.id, text):
        mins = minutes_left_for_date(user.id, text)
        await update.message.reply_text(f"С этой датой уже работаем. Попробуй другую или через {mins} мин.")
        return

    program = context.user_data.get("program") or DEFAULT_PROGRAM

    try:
        arcana = calculate_arcana(text, program)
    except Exception:
        await update.message.reply_text("Дата кривая. Нужен формат ДД.ММ.ГГГГ.")
        return

    # достаём PDF и шлём одним сообщением
    try:
        guide_path = get_guide(program, arcana)
        if not guide_path:
            await update.message.reply_text("Гайд отсутствует.")
            if ADMIN_CHAT_ID:
                await admin_notify(context, f"НЕ ВЫДАНО (нет файла): {fmt_user(user)} — {program}/{arcana}.pdf")
            return

        caption = f"Твой аркан {arcana}. Держи свой гайд."
        with open(guide_path, "rb") as f:
            await update.message.reply_document(document=f, caption=caption)

        # лог только по факту
        record_success_date(user.id, text)
        if ADMIN_CHAT_ID:
            await admin_notify(context, f"ВЫДАНО: {fmt_user(user)} — {program}/{arcana}.pdf")

    except Exception as e:
        await update.message.reply_text("Не получилось выдать файл.")
        if ADMIN_CHAT_ID:
            await admin_notify(context, f"ОШИБКА ВЫДАЧИ: {fmt_user(user)} — {program}/{arcana}.pdf — {e}")

async def on_noise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Любые нерелевантные сообщения: мягко направляем и ограничиваем спам."""
    user = update.effective_user
    txt = (update.message.text or "").strip()
    record_noise(user.id, txt)
    if noise_too_often(user.id):
        await update.message.reply_text("Хватит спама. Жду дату в формате ДД.ММ.ГГГГ.")
    else:
        await update.message.reply_text("Жду дату в формате ДД.ММ.ГГГГ. Пример: 01.06.1926")

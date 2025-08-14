import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import CODEWORDS, DATE_RE, ADMIN_CHAT_ID
from arcana_calculator import calculate_arcana
from antispam import can_issue, minutes_left, mark_issue
from gdrive_integration import get_guide
from utils import admin_notify, fmt_user

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Поддерживаем и русские, и латиницу
ALIAS = {
    "капуста": "kapusta", "kapusta": "kapusta",
    "аватар": "avatar", "avatar": "avatar",
    "амурчик": "amourchik", "амurchik": "amourchik", "amourchik": "amourchik",
}

def _program_from_args(args) -> str:
    if not args:
        return CODEWORDS.get("kapusta", "kapusta")
    key = (args[0] or "").strip().lower()
    return ALIAS.get(key, CODEWORDS.get(key, CODEWORDS.get("kapusta", "kapusta")))

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    program = _program_from_args(context.args)
    context.user_data["program"] = program

    await update.message.reply_text(
        "Кидай дату рождения в формате ДД.ММ.ГГГГ — пришлю один файл: "
        "«Ваш аркан N — вот ваш гайд». "
        f"Код: {program}"
    )

    if ADMIN_CHAT_ID:
        await admin_notify(context, f"▶️ /start {program} от {fmt_user(user)}")

async def on_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (update.message.text or "").strip()

    # Формат даты
    if not DATE_RE.match(text):
        await update.message.reply_text("Нужен формат ДД.ММ.ГГГГ. Пример: 01.06.1926")
        return

    # Антиспам
    if not can_issue(user.id):
        await update.message.reply_text(f"Где-то торопимся. Попробуй позже. Минут до разблокировки: {minutes_left(user.id)}.")
        return

    program = context.user_data.get("program") or CODEWORDS.get("kapusta", "kapusta")

    # Счёт аркана по матрице с учётом направления
    try:
        arcana = calculate_arcana(text, program)
    except Exception:
        await update.message.reply_text("Дата кривая. Давай по-честному: ДД.ММ.ГГГГ.")
        return

    # Достаём PDF и шлём ОДНИМ сообщением
    try:
        guide_path = get_guide(program, arcana)
        if not guide_path:
            await update.message.reply_text("Гайд отсутствует.")
            if ADMIN_CHAT_ID:
                await admin_notify(context, f"❗️ Нет файла для {program}/{arcana}.pdf у {fmt_user(user)}")
            return

        caption = f"{program.capitalize()}: аркан {arcana}. Держи свой гайд."
        with open(guide_path, "rb") as f:
            await update.message.reply_document(document=f, caption=caption)

        # отмечаем успешную выдачу как использование
        mark_issue(user.id)

        if ADMIN_CHAT_ID:
            await admin_notify(context, f"✅ Выдан {program}/{arcana}.pdf для {fmt_user(user)}")

    except Exception as e:
        await update.message.reply_text("Не получилось выдать файл.")
        if ADMIN_CHAT_ID:
            await admin_notify(context, f"🔥 Ошибка выдачи {program}/{arcana}.pdf для {fmt_user(user)}: {e}")

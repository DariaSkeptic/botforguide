from telegram import Update
from telegram.ext import ContextTypes
import logging
from gdrive_integration import get_guide
from arcana_calculator import calculate_arcana
from antispam import can_issue
from config import ADMIN_CHAT_ID

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info(f"Команда /start вызвана пользователем {user.username} ({user.id})")
    await update.message.reply_text(f"Привет, {user.first_name}. Кидай дату рождения в формате ДД.ММ.ГГГГ.")
    if ADMIN_CHAT_ID:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"🟡 Старт сценария от {user.username} ({user.id})")

async def on_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text.strip()
    program = context.args[0] if context.args else "kapusta"
    
    if can_issue(user.id):
        try:
            arcana = calculate_arcana(text)
            guide_path = get_guide(program, arcana)
            if guide_path:
                with open(guide_path, 'rb') as guide_file:
                    await update.message.reply_document(document=guide_file, caption=f"{program.capitalize()}: аркан {arcana}. Держи свой гайд.")
                if ADMIN_CHAT_ID:
                    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"✅ Выдан гайд {program} аркан {arcana} для {user.username} ({user.id})")
            else:
                await update.message.reply_text("Гайд отсутствует")
                if ADMIN_CHAT_ID:
                    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"❗️ Гайд отсутствует для {program} аркан {arcana}, {user.username} ({user.id})")
        except Exception as e:
            await update.message.reply_text("Не получилось выдать файл")
            if ADMIN_CHAT_ID:
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"🔥 Ошибка выдачи для {user.username} ({user.id}): {str(e)}")
    else:
        await update.message.reply_text("Слишком много запросов, попробуй позже")
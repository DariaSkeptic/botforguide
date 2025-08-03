import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)

GUIDES_FOLDER = "guides"
ASK_DATE = 1

# Функция для чтения .env файла и загрузки переменных окружения
def load_env():
    env_path = '.env'
    if not os.path.exists(env_path):
        raise FileNotFoundError(".env file not found")
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key_value = line.split('=', 1)
                if len(key_value) == 2:
                    key, value = key_value
                    os.environ[key.strip()] = value.strip()

# Загружаем переменные окружения
load_env()
TOKEN = os.getenv("BOT_TOKEN")

def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧮 Рассчитать аркан", callback_data="calculate")],
        [InlineKeyboardButton("🔁 Перезапуск", callback_data="restart"),
         InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = get_main_menu()
    user = update.effective_user
    name = user.first_name if user.first_name else user.username if user.username else "друг"

    welcome_text = (
        f"🔮 Привет, {name}!\n"
        "Я бот, который поможет тебе узнать, как тебя воспринимают в обществе — через аркан судьбы.\n\n"
        "Нажми кнопку ниже, чтобы начать расчёт:"
    )

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=keyboard)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(welcome_text, reply_markup=keyboard)

    return ConversationHandler.END

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "calculate":
        await query.message.reply_text("Введи свою дату рождения в формате: ДД.ММ.ГГГГ")
        return ASK_DATE

    elif action == "restart":
        return await start(update, context)

    elif action == "help":
        await query.message.reply_text(
            "📌 Инструкция:\n\n"
            "1. Нажми \"Рассчитать аркан\"\n"
            "2. Введи свою дату рождения (например: 14.08.1990)\n"
            "3. Получи свой аркан и гайд в PDF\n\n"
            "Нажми \"Перезапуск\", чтобы начать заново",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END

async def calculate_arcan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        day = int(text.split(".")[0])
        if not (1 <= day <= 31):
            raise ValueError("Неверный день")

        if day <= 22:
            arcan_number = day
        else:
            digit_sum = sum(int(d) for d in str(day))
            while digit_sum > 22:
                digit_sum = sum(int(d) for d in str(digit_sum))
            arcan_number = digit_sum

        guide_path = os.path.join(GUIDES_FOLDER, f"{arcan_number}.pdf")
        if os.path.exists(guide_path):
            await update.message.reply_text(f"Ваш аркан: {arcan_number}. Сейчас отправлю гайд...")
            with open(guide_path, "rb") as file:
                await update.message.reply_document(file)
        else:
            await update.message.reply_text("Гайд не найден 😢. Напиши админу.")
    except Exception:
        await update.message.reply_text("Некорректный формат. Введите дату как: 12.05.1995")

    await update.message.reply_text("Если хочешь рассчитать снова, нажми кнопку ниже:",
                                    reply_markup=get_main_menu())
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_handler, pattern="^(calculate|restart|help)$")],
        states={ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, calculate_arcan)]},
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.run_polling()

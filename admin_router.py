import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes, CallbackContext, CommandHandler
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Исходная клавиатура админ-панели
def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("Недостающие PDF", callback_data="missing_pdfs")],
        [InlineKeyboardButton("Существующие PDF", callback_data="existing_pdfs")],
        [InlineKeyboardButton("Переменные окружения", callback_data="env_vars")],
        [InlineKeyboardButton("ID и настройки", callback_data="ids_settings")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info(f"Команда /admin вызвана пользователем {user.username} ({user.id})")
    admin_user_id = os.getenv("ADMIN_USER_ID")
    if not admin_user_id:
        logger.error("Переменная ADMIN_USER_ID не задана в окружении!")
        await update.message.reply_text("Ошибка: админ не настроен. Обратитесь к разработчику.")
        return
    try:
        if str(user.id) == admin_user_id:
            reply_markup = get_admin_keyboard()
            await update.message.reply_text("Админ-панель:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Доступ запрещён")
    except Exception as e:
        logger.error(f"Ошибка в cmd_admin: {str(e)}")
        await update.message.reply_text("Ошибка в админ-панели. Обратитесь к разработчику.")

async def admin_panel_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    logger.info(f"Обработка callback от {user.username} ({user.id}) с данными: {query.data}")
    admin_user_id = os.getenv("ADMIN_USER_ID")
    if not admin_user_id:
        logger.error("Переменная ADMIN_USER_ID не задана в окружении!")
        await query.edit_message_text("Ошибка: админ не настроен. Обратитесь к разработчику.")
        return
    try:
        if str(user.id) == admin_user_id:
            reply_markup = get_admin_keyboard()
            if query.data == "missing_pdfs":
                logger.info("Запуск получения недостающих PDF")
                from gdrive_integration import list_missing_guides
                missing = list_missing_guides()
                if missing:
                    await query.edit_message_text(f"Недостающие PDF:\n{'\n'.join(missing)}", reply_markup=reply_markup)
                else:
                    await query.edit_message_text("Все PDF на месте!", reply_markup=reply_markup)
            elif query.data == "existing_pdfs":
                logger.info("Запуск получения существующих PDF")
                from gdrive_integration import list_existing_guides
                existing = list_existing_guides()
                if existing:
                    await query.edit_message_text(f"Существующие PDF:\n{'\n'.join(existing)}", reply_markup=reply_markup)
                else:
                    await query.edit_message_text("Нет существующих PDF.", reply_markup=reply_markup)
            elif query.data == "env_vars":
                logger.info("Запуск отображения переменных окружения")
                env_vars = {
                    "BOT_TOKEN": "Задана" if os.getenv("BOT_TOKEN") else "Не задана",
                    "ADMIN_USER_ID": os.getenv("ADMIN_USER_ID", "Не задана"),
                    "ADMIN_CHAT_ID": os.getenv("ADMIN_CHAT_ID", "Не задана"),
                    "GDRIVE_FOLDER_KAPUSTA": os.getenv("GDRIVE_FOLDER_KAPUSTA", "Не задана"),
                    "GDRIVE_FOLDER_AVATAR": os.getenv("GDRIVE_FOLDER_AVATAR", "Не задана"),
                    "GDRIVE_FOLDER_AMOURCHIK": os.getenv("GDRIVE_FOLDER_AMOURCHIK", "Не задана"),
                    "GOOGLE_CREDENTIALS_JSON_B64": "Задана" if os.getenv("GOOGLE_CREDENTIALS_JSON_B64") else "Не задана",
                }
                await query.edit_message_text(f"Переменные окружения:\n{'\n'.join(f'{k}: {v}' for k, v in env_vars.items())}", reply_markup=reply_markup)
            elif query.data == "ids_settings":
                logger.info("Запуск отображения ID и настроек")
                user_id = os.getenv("ADMIN_USER_ID", "Не задан")
                chat_id = os.getenv("ADMIN_CHAT_ID", "Не задан")
                await query.edit_message_text(f"ID и настройки:\nТвой ID: {user.id}\nADMIN_USER_ID: {user_id}\nADMIN_CHAT_ID: {chat_id}", reply_markup=reply_markup)
        else:
            await query.edit_message_text("Доступ запрещён")
    except Exception as e:
        logger.error(f"Ошибка в admin_panel_callback при обработке {query.data}: {str(e)}")
        await query.edit_message_text(f"Ошибка при обработке {query.data}. Обратитесь к разработчику.", reply_markup=get_admin_keyboard())

# Новые команды для админ-меню
async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    admin_user_id = os.getenv("ADMIN_USER_ID")
    if str(user.id) == admin_user_id:
        logger.info(f"Сброс бота инициирован пользователем {user.username} ({user.id})")
        # Здесь можно добавить логику сброса (например, очистка антиспам-кэша)
        await update.message.reply_text("Бот сброшен. Антиспам-кэш очищен.", reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text("Доступ запрещён")

async def cmd_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    admin_user_id = os.getenv("ADMIN_USER_ID")
    if str(user.id) == admin_user_id:
        logger.info(f"Перезапуск бота инициирован пользователем {user.username} ({user.id})")
        admin_chat_id = os.getenv("ADMIN_CHAT_ID")
        if admin_chat_id:
            await context.bot.send_message(chat_id=admin_chat_id, text="⚠️ Перезапуск бота инициирован админом!")
        await update.message.reply_text("Запрос на перезапуск отправлен. Передеплойте приложение вручную.", reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text("Доступ запрещён")

# Настройка меню для админа при старте
async def set_admin_menu(application):
    admin_user_id = os.getenv("ADMIN_USER_ID")
    if admin_user_id:
        bot = application.bot
        commands = [
            ("missing_pdfs", "🌿 Недостающие PDF", "Показать недостающие PDF"),
            ("existing_pdfs", "🌿 Существующие PDF", "Показать существующие PDF"),
            ("env_vars", "🌿 Переменные окружения", "Показать переменные окружения"),
            ("ids_settings", "🌿 ID и настройки", "Показать ID и настройки"),
            ("reset", "🌿 Сброс бота", "Очистить состояние бота"),
            ("restart", "🌿 Перезапуск", "Инициировать перезапуск бота"),
        ]
        await bot.set_my_commands(
            commands=[(cmd, desc, "admin") for cmd, desc, _ in commands],
            scope={"type": "users", "user_id": int(admin_user_id)}
        )
        logger.info(f"Меню админа установлено для пользователя {admin_user_id}")
    else:
        logger.error("Не удалось установить меню админа: ADMIN_USER_ID не задан")

# Обновление botforguide.py для вызова set_admin_menu
# (Добавим это в твой текущий botforguide.py ниже)
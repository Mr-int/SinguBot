import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler
from functools import wraps
from sheets_handler import GoogleSheetsHandler

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Google Sheets
sheets_handler = GoogleSheetsHandler(
    credentials_path='credentials.json',
    spreadsheet_id=os.getenv('SPREADSHEET_ID')
)

REGISTERING = 1
ADDING_LEAD = 2
LEAD_INFO = 3
LEAD_PHONE = 4
LEAD_PARENT = 5
LEAD_PARENT_PHONE = 6
LEAD_PARENT_PHONE2 = 7
BROADCAST_TEXT = 8
BROADCAST_CONFIRM = 9

ADMIN_IDS = [641057657, 6466769330]

def admin_only(func):
    """Decorator to restrict access to admin commands."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("У вас нет доступа к этой команде.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def get_all_chat_ids():
    """Fetches all non-null chat_ids from the participants table."""
    participants = sheets_handler.get_all_participants()
    chat_ids = [p['chat_id'] for p in participants if p['chat_id']]
    return chat_ids

def get_main_keyboard():
    """Create main menu keyboard."""
    keyboard = [
        [KeyboardButton("ℹ️ О конкурсе"), KeyboardButton("👤 Моя статистика")],
        [KeyboardButton("➕ Добавить лида"), KeyboardButton("📱 Информация для продвижения")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_contact_keyboard():
    """Create keyboard with contact button."""
    keyboard = [[KeyboardButton("📱 Отправить контакт", request_contact=True)]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def show_registration_prompt(update: Update):
    """Sends the registration prompt."""
    welcome_text = (
        "| /start |\n\n"
        "Внимание! Обнаружен студент IT-колледжа!\n"
        "Я - бот, который поможет тебе заполучить главный приз в конкурсе\n\n"
        "Теперь о правилах участия:\n\n"
        "Для участия в конкурсе необходимо зарегистрироваться.\n"
        "Нажмите кнопку ниже, чтобы начать регистрацию."
    )
    keyboard = [[InlineKeyboardButton("📝 Зарегистрироваться", callback_data="register")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Простая регистрация: если пользователь есть в базе — меню, если нет — регистрация."""
    telegram_id = update.effective_user.id

    participant = sheets_handler.find_participant_by_telegram_id(telegram_id)

    if participant:
        if not participant['chat_id']:
            sheets_handler.update_participant_chat_id(telegram_id, update.effective_chat.id)
        await update.message.reply_text(
            "С возвращением! Используйте меню для навигации:",
            reply_markup=get_main_keyboard()
        )
    else:
        # Дополнительно проверяем Google-таблицу (на всякий случай)
        in_sheet = False
        try:
            row = sheets_handler.find_participant_by_telegram_id(telegram_id)
            if row:
                in_sheet = True
        except Exception as e:
            logger.error(f"Ошибка при поиске пользователя в Google Sheets: {e}")
            in_sheet = False
        # Если нет ни в базе, ни в таблице — регистрация
        await show_registration_prompt(update)

async def register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "Для регистрации, пожалуйста, отправь:\n"
        "1. ФИО\n"
        "2. Курс обучения (1-4)\n\n"
        "Пример ввода✅:\n"
        "Иванов Иван Иванович\n"
        "1"
    )
    return REGISTERING

async def process_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        full_name, course = update.message.text.split('\n')
        course = int(course)
        
        if not (1 <= course <= 4):
            await update.message.reply_text(
                "❌ Курс должен быть от 1 до 4. Попробуйте снова.\n\n"
                "Пример ввода✅:\n"
                "Иванов Иван Иванович\n"
                "1"
            )
            return REGISTERING
        
        # Получаем максимальный ID из Google-таблицы
        max_sheet_id = sheets_handler.get_max_id()
        new_id = max(max_sheet_id, 1) + 1

        # Добавляем участника в Google таблицу
        try:
            sheets_handler.add_participant(new_id, full_name, course, update.effective_chat.id, update.effective_user.id)
        except Exception as e:
            logger.error(f"Ошибка при добавлении строки в Google Sheets: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при добавлении в Google-таблицу. Попробуйте позже!"
            )
            return ConversationHandler.END
        
        await update.message.reply_text(
            "✅ Регистрация успешно завершена!",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, отправьте информацию в правильном формате:\n\n"
            "Пример ввода✅:\n"
            "Иванов Иван Иванович\n"
            "1"
        )
        return REGISTERING

async def add_lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = sheets_handler.find_participant_by_telegram_id(update.effective_user.id)
    
    if not user:
        await update.message.reply_text(
            "❌ Сначала зарегистрируйтесь через кнопку '📝 Зарегистрироваться' в главном меню"
        )
        return ConversationHandler.END
    
    keyboard = [
        [
            InlineKeyboardButton("4-8 класс (Кэмп/ДО)", callback_data="lead_camp_do"),
            InlineKeyboardButton("9 класс (Колледж)", callback_data="lead_college")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите тип программы для нового лида:\n\n"
        "Для отмены используйте команду /cancel",
        reply_markup=reply_markup
    )
    return ADDING_LEAD

async def lead_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['lead_type'] = query.data
    
    await query.edit_message_text(
        "Пожалуйста, отправьте информацию о лиде в следующем формате:\n\n"
        "ФИО ученика\n"
        "Возраст (только число)\n"
        "Класс (только число)\n\n"
        "Пример ввода✅:\n"
        "Иванов Иван Иванович\n"
        "14\n"
        "8\n\n"
        "Для отмены используйте команду /cancel"
    )
    return LEAD_INFO

async def process_lead_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        info = update.message.text.split('\n')
        if len(info) != 3:
            raise ValueError
        
        full_name, age, grade = info
        age = int(age)
        grade = int(grade)
        
        if not (4 <= grade <= 9):
            await update.message.reply_text(
                "❌ Класс должен быть от 4 до 9. Попробуйте снова.\n\n"
                "Пример ввода✅:\n"
                "Иванов Иван Иванович\n"
                "14\n"
                "8"
            )
            return LEAD_INFO
        
        context.user_data['lead_full_name'] = full_name
        context.user_data['lead_age'] = age
        context.user_data['lead_grade'] = grade
        
        await update.message.reply_text(
            "Теперь отправьте username ученика в Telegram (без @):\n\n"
            "Если username отсутствует, отправьте 'нет'\n\n"
            "Для отмены используйте команду /cancel"
        )
        return LEAD_PHONE
        
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, отправьте информацию в правильном формате:\n\n"
            "Пример ввода✅:\n"
            "Иванов Иван Иванович\n"
            "14\n"
            "8"
        )
        return LEAD_INFO

async def process_lead_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip()
    
    if username.lower() == 'нет':
        username = "Не указан"
    elif not username.startswith('@'):
        username = '@' + username
    
    context.user_data['lead_telegram'] = username
    
    await update.message.reply_text(
        "Теперь отправьте номер телефона ученика в формате:\n"
        "+7XXXXXXXXXX или 8XXXXXXXXXX\n\n"
        "Для отмены используйте команду /cancel"
    )
    return LEAD_PARENT

async def process_lead_parent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not (phone.startswith('+7') or phone.startswith('8')):
        await update.message.reply_text(
            "❌ Неверный формат номера телефона.\n"
            "Пожалуйста, отправьте номер в формате:\n"
            "+7XXXXXXXXXX или 8XXXXXXXXXX\n\n"
            "Для отмены используйте команду /cancel"
        )
        return LEAD_PARENT

    digits_only = ''.join(filter(str.isdigit, phone))
    if len(digits_only) != 11:
        await update.message.reply_text(
            "❌ Неверная длина номера телефона.\n"
            "Пожалуйста, отправьте номер в формате:\n"
            "+7XXXXXXXXXX или 8XXXXXXXXXX\n\n"
            "Для отмены используйте команду /cancel"
        )
        return LEAD_PARENT

    context.user_data['lead_phone'] = phone
    await update.message.reply_text(
        "Теперь отправьте ФИО родителя:\n\nДля отмены используйте команду /cancel"
    )
    return LEAD_PARENT_PHONE

async def process_lead_parent_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parent_name = update.message.text.strip()
    context.user_data['lead_parent'] = parent_name
    await update.message.reply_text(
        "Теперь отправьте номер телефона родителя в формате:\n+7XXXXXXXXXX или 8XXXXXXXXXX\n\nДля отмены используйте команду /cancel"
    )
    return LEAD_PARENT_PHONE2  # Новый шаг для номера телефона родителя

async def process_lead_parent_phone2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parent_phone = update.message.text.strip()
        # Проверяем формат номера телефона
        if not (parent_phone.startswith('+7') or parent_phone.startswith('8')):
            await update.message.reply_text(
                "❌ Неверный формат номера телефона.\n"
                "Пожалуйста, отправьте номер в формате:\n"
                "+7XXXXXXXXXX или 8XXXXXXXXXX\n\n"
                "Для отмены используйте команду /cancel"
            )
            return LEAD_PARENT_PHONE2
        digits_only = ''.join(filter(str.isdigit, parent_phone))
        if len(digits_only) != 11:
            await update.message.reply_text(
                "❌ Неверная длина номера телефона.\n"
                "Пожалуйста, отправьте номер в формате:\n"
                "+7XXXXXXXXXX или 8XXXXXXXXXX\n\n"
                "Для отмены используйте команду /cancel"
            )
            return LEAD_PARENT_PHONE2
        if parent_phone.startswith('8'):
            parent_phone = '+7' + parent_phone[1:]
        user = sheets_handler.find_participant_by_telegram_id(update.effective_user.id)
        
        if user and (len(user) > 16 and not user[16]):
            sheets_handler.update_participant_chat_id(update.effective_user.id, update.effective_chat.id)
        
        if not user:
             await update.message.reply_text("Пожалуйста, сначала зарегистрируйтесь, используя команду /start.")
             return ConversationHandler.END

        # Создаем нового лида
        lead_data = {
            'child_name': context.user_data['lead_full_name'],
            'age': context.user_data['lead_age'],
            'grade': context.user_data['lead_grade'],
            'telegram': context.user_data['lead_telegram'],
            'phone': context.user_data['lead_phone'],
            'parent_name': context.user_data['lead_parent'],
            'parent_phone': parent_phone,
            'program_type': context.user_data['lead_type']
        }
        sheets_handler.add_lead(user[1], lead_data)
        await update.message.reply_text(
            "✅ Лид добавлен успешно! Баллы будут начислены администратором после проверки.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in process_lead_parent_phone2: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при сохранении данных. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show competition rules."""
    rules_text = (
        "📋 Правила участия в конкурсе:\n\n"
        "1. Зарегистрируйся как участник\n"
        "2. Приводи новых учеников\n"
        "3. Получай баллы за каждого привлеченного ученика:\n"
        "   • 5 баллов за ученика 4-8 класса (Кэмп/ДО)\n"
        "   • 10 баллов за ученика 9 класса (Колледж)\n"
        "4. Следи за своим рейтингом\n"
        "5. Используй материалы для продвижения"
    )
    await update.message.reply_text(rules_text)

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show information about Singularity programs."""
    keyboard = [
        [
            InlineKeyboardButton("Курсы", callback_data="info_courses"),
            InlineKeyboardButton("Лагерь", callback_data="info_camp")
        ],
        [
            InlineKeyboardButton("Колледж-школа", callback_data="info_college"),
            InlineKeyboardButton("Приемная комиссия", callback_data="info_admission")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите категорию информации:",
        reply_markup=reply_markup
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает статистику участника."""
    user_id = update.effective_user.id
    
    sheet_user_row = sheets_handler.find_participant_by_telegram_id(user_id)
    
    if not sheet_user_row:
        await update.message.reply_text(
            "Вы не зарегистрированы в системе. Используйте /start для регистрации."
        )
        return ConversationHandler.END
        
    full_name = sheet_user_row[2]
    course = sheet_user_row[3]

    # Получаем баллы из Google Sheets
    points = sheets_handler.get_participant_points(sheet_user_row[1])
    
    # Получаем лиды из Google Sheets
    leads = sheets_handler.get_all_leads(sheet_user_row[1])
    
    # Формируем сообщение со статистикой
    message = (
        f"📊 Ваша статистика:\n\n"
        f"👤 ФИО: {full_name}\n"
        f"🎓 Курс: {course}\n"
        f"⭐️ Баллы: {points}\n\n"
        f"👥 Ваши лиды:\n\n"
    )
    
    if leads:
        for lead in leads:
            message += f"{lead['child_name']}\n"
    else:
        message += "У вас пока нет лидов"
    
    await update.message.reply_text(message)
    return ConversationHandler.END

async def info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    info = PROGRAM_INFO[query.data]
    await query.edit_message_text(
        f"{info['title']}\n\n{info['text']}"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Операция отменена",
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END

# --- Admin Panel & Broadcast Functions ---

@admin_only
async def root(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel entry point."""
    keyboard = [[InlineKeyboardButton("Начать рассылку", callback_data="start_broadcast")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Админ-панель:", reply_markup=reply_markup)

async def start_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks for the broadcast message text."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Пожалуйста, введите текст для рассылки.")
    return BROADCAST_TEXT

async def get_broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows a preview of the broadcast message."""
    broadcast_text = update.message.text
    context.user_data['broadcast_text'] = broadcast_text

    # Show preview
    await update.message.reply_text("<b>Пример рассылки:</b>", parse_mode='HTML')
    await update.message.reply_text(broadcast_text)

    keyboard = [
        [
            InlineKeyboardButton("✅ Начать", callback_data="confirm_broadcast"),
            InlineKeyboardButton("❌ Отменить", callback_data="cancel_broadcast")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Вы уверены, что хотите начать рассылку с этим текстом?",
        reply_markup=reply_markup
    )
    return BROADCAST_CONFIRM

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the message to all users."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Рассылка начата...")

    broadcast_text = context.user_data['broadcast_text']
    chat_ids = get_all_chat_ids()
    
    successful_sends = 0
    failed_sends = 0

    for chat_id in chat_ids:
        try:
            await context.bot.send_message(chat_id=chat_id, text=broadcast_text)
            successful_sends += 1
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
            failed_sends += 1
    
    await query.message.reply_text(
        f"✅ Рассылка завершена!\n"
        f"Успешно отправлено: {successful_sends}\n"
        f"Не удалось отправить: {failed_sends}"
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the broadcast conversation."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Рассылка отменена.")
    context.user_data.clear()
    return ConversationHandler.END

def main():
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    # Conversation handlers
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('user', register_callback),
            CallbackQueryHandler(register_callback, pattern="^register$")
        ],
        states={
            REGISTERING: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_registration)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    lead_handler = ConversationHandler(
        entry_points=[
            CommandHandler('add', add_lead),
            MessageHandler(filters.Regex("^➕ Добавить лида$"), add_lead)
        ],
        states={
            ADDING_LEAD: [CallbackQueryHandler(lead_callback)],
            LEAD_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_lead_info)],
            LEAD_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_lead_phone)],
            LEAD_PARENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_lead_parent)],
            LEAD_PARENT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_lead_parent_phone)],
            LEAD_PARENT_PHONE2: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_lead_parent_phone2)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    broadcast_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast_callback, pattern="^start_broadcast$")],
        states={
            BROADCAST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_broadcast_text)],
            BROADCAST_CONFIRM: [
                CallbackQueryHandler(send_broadcast, pattern="^confirm_broadcast$"),
                CallbackQueryHandler(cancel_broadcast, pattern="^cancel_broadcast$")
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel_broadcast)]
    )

    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(lead_handler)
    application.add_handler(broadcast_handler)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("root", root))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ О конкурсе$"), about))
    application.add_handler(MessageHandler(filters.Regex("^📱 Информация для продвижения$"), info))
    application.add_handler(MessageHandler(filters.Regex("^👤 Моя статистика$"), stats))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(info_callback, pattern="^info_"))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

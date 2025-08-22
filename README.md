# Ambassador Singularity Bot

Telegram bot for managing the Singularity ambassador program, helping students track their referrals and earn points.

## ✅ Исправленные проблемы

- **Неправильное размещение данных** - баллы теперь записываются в правильную колонку
- **Отсутствие автоматического начисления баллов** - система работает автоматически
- **Ошибки чтения данных** - исправлены методы для корректной работы с таблицей

## Features
- Participant registration
- Lead tracking and registration
- Information sharing about Singularity programs
- Points tracking and statistics
- Push notifications
- **Автоматическое начисление баллов** за привлеченных учеников

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Telegram bot token and Google Sheets ID:
```
BOT_TOKEN=your_bot_token_here
SPREADSHEET_ID=your_spreadsheet_id_here
```

3. Create `credentials.json` file for Google Sheets API access

4. Run the bot:
```bash
python bot.py
```

## Commands
- `/start` - Start the bot and see welcome message
- `/about` - View competition rules
- `/user` - Register as a participant
- `/add` - Add a new lead
- `/info` - Get information about Singularity programs
- `/stats` - View your points and ranking

## 📊 Система баллов

- **5 баллов** за ученика 4-8 класса (Кэмп/ДО)
- **10 баллов** за ученика 9 класса (Колледж)
- Баллы начисляются автоматически при добавлении лида

## 🔧 Дополнительные инструменты

- `fix_table.py` - Скрипт для исправления структуры существующей таблицы
- `SETUP.md` - Подробные инструкции по настройке 
#!/usr/bin/env python3
"""
Скрипт для проверки подключения к Google Sheets и тестирования основных функций.
"""

import os
from dotenv import load_dotenv
from sheets_handler import GoogleSheetsHandler

def test_google_sheets_connection():
    """Тестирует подключение к Google Sheets."""
    
    print("🔍 Тестирование подключения к Google Sheets...")
    
    # Проверяем наличие необходимых файлов
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("   Создайте файл .env с переменными BOT_TOKEN и SPREADSHEET_ID")
        return False
    
    if not os.path.exists('credentials.json'):
        print("❌ Файл credentials.json не найден!")
        print("   Скачайте файл с ключами из Google Cloud Console")
        return False
    
    # Загружаем переменные окружения
    load_dotenv()
    
    spreadsheet_id = os.getenv('SPREADSHEET_ID')
    if not spreadsheet_id:
        print("❌ SPREADSHEET_ID не найден в файле .env!")
        return False
    
    print(f"✅ SPREADSHEET_ID найден: {spreadsheet_id}")
    
    try:
        # Инициализируем Google Sheets
        sheets_handler = GoogleSheetsHandler(
            credentials_path='credentials.json',
            spreadsheet_id=spreadsheet_id
        )
        
        print("✅ Подключение к Google Sheets установлено")
        
        # Тестируем чтение данных
        print("📖 Тестирование чтения данных...")
        
        result = sheets_handler.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='A:R'
        ).execute()
        
        values = result.get('values', [])
        print(f"✅ Прочитано {len(values)} строк из таблицы")
        
        if len(values) > 0:
            print(f"📊 Заголовки таблицы: {values[0]}")
            
            if len(values) > 1:
                print(f"📝 Первая строка данных: {values[1]}")
        
        # Тестируем поиск участника
        print("🔍 Тестирование поиска участника...")
        test_telegram_id = 123456789  # Тестовый ID
        participant = sheets_handler.find_participant_by_telegram_id(test_telegram_id)
        
        if participant:
            print(f"✅ Участник найден: {participant}")
        else:
            print("ℹ️ Участник с тестовым ID не найден (это нормально)")
        
        print("\n🎉 Все тесты пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при подключении к Google Sheets: {e}")
        print("\n🔧 Возможные причины:")
        print("1. Неправильный SPREADSHEET_ID")
        print("2. Недостаточно прав у Service Account")
        print("3. Google Sheets API не включен")
        print("4. Неправильный формат credentials.json")
        return False

def test_bot_token():
    """Тестирует наличие токена бота."""
    
    print("\n🤖 Проверка токена бота...")
    
    load_dotenv()
    bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token:
        print("❌ BOT_TOKEN не найден в файле .env!")
        return False
    
    if bot_token == 'your_bot_token_here':
        print("❌ BOT_TOKEN не настроен (используется значение по умолчанию)")
        return False
    
    print("✅ BOT_TOKEN найден")
    return True

def main():
    """Основная функция тестирования."""
    
    print("🚀 Тестирование SinguBot")
    print("=" * 40)
    
    # Тестируем токен бота
    bot_ok = test_bot_token()
    
    # Тестируем Google Sheets
    sheets_ok = test_google_sheets_connection()
    
    print("\n" + "=" * 40)
    print("📋 Результаты тестирования:")
    print(f"🤖 Telegram Bot: {'✅' if bot_ok else '❌'}")
    print(f"📊 Google Sheets: {'✅' if sheets_ok else '❌'}")
    
    if bot_ok and sheets_ok:
        print("\n🎉 Все готово для запуска бота!")
        print("   Запустите: python bot.py")
    else:
        print("\n⚠️ Есть проблемы, которые нужно исправить перед запуском")
        print("   Смотрите SETUP.md для подробных инструкций")

if __name__ == "__main__":
    main()

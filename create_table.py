#!/usr/bin/env python3
"""
Скрипт для создания Google таблицы с правильной структурой для SinguBot.
"""

import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

def create_spreadsheet():
    """Создает новую Google таблицу с правильной структурой."""
    
    print("🚀 Создание новой Google таблицы для SinguBot...")
    
    # Проверяем наличие credentials.json
    if not os.path.exists('credentials.json'):
        print("❌ Файл credentials.json не найден!")
        print("   Скачайте файл с ключами из Google Cloud Console")
        return None
    
    try:
        # Инициализируем Google Sheets API
        credentials = service_account.Credentials.from_service_account_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        
        print("✅ Подключение к Google API установлено")
        
        # Создаем новую таблицу
        spreadsheet = {
            'properties': {
                'title': 'SinguBot - Программа амбассадоров'
            },
            'sheets': [
                {
                    'properties': {
                        'title': 'Участники',
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': 18
                        }
                    }
                }
            ]
        }
        
        spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = spreadsheet['spreadsheetId']
        
        print(f"✅ Таблица создана! ID: {spreadsheet_id}")
        print(f"🔗 Ссылка: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        
        # Добавляем заголовки
        headers = [
            'ID', 'ID_участника', 'ФИО', 'Курс', 'Имя_ребенка', 'Возраст', 'Класс',
            'Telegram', 'Телефон_ученика', 'ФИО_родителя', 'Телефон_родителя',
            'Баллы', 'Статус', 'Дата_добавления', 'Программа', 'Комментарий',
            'Chat_ID', 'Telegram_ID'
        ]
        
        # Форматируем заголовки
        header_format = {
            'backgroundColor': {
                'red': 0.2,
                'green': 0.6,
                'blue': 0.9
            },
            'textFormat': {
                'bold': True,
                'foregroundColor': {
                    'red': 1.0,
                    'green': 1.0,
                    'blue': 1.0
                }
            },
            'horizontalAlignment': 'CENTER'
        }
        
        # Применяем заголовки
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='A1:R1',
            valueInputOption='RAW',
            body={'values': [headers]}
        ).execute()
        
        # Применяем форматирование к заголовкам
        requests = [
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 18
                    },
                    'cell': {
                        'userEnteredFormat': header_format
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                }
            },
            {
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 18
                    }
                }
            }
        ]
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        print("✅ Заголовки добавлены и отформатированы")
        
        # Делаем таблицу доступной для редактирования
        service_account_email = credentials.service_account_email
        
        # Получаем информацию о таблице
        file_metadata = drive_service.files().get(fileId=spreadsheet_id).execute()
        
        # Устанавливаем права доступа
        permission = {
            'type': 'anyone',
            'role': 'writer'
        }
        
        drive_service.permissions().create(
            fileId=spreadsheet_id,
            body=permission
        ).execute()
        
        print(f"✅ Таблица доступна для редактирования")
        print(f"📧 Service Account: {service_account_email}")
        
        # Сохраняем ID в .env файл
        env_content = f"""# Telegram Bot Token
BOT_TOKEN=your_bot_token_here

# Google Sheets ID
SPREADSHEET_ID={spreadsheet_id}

# Google Service Account Credentials
GOOGLE_CREDENTIALS_FILE=credentials.json
"""
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ ID таблицы сохранен в файл .env")
        
        return spreadsheet_id
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблицы: {e}")
        return None

def main():
    """Основная функция."""
    
    print("🔧 Создание Google таблицы для SinguBot")
    print("=" * 50)
    
    print("⚠️ Внимание: Этот скрипт создаст новую таблицу!")
    print("   Если у вас уже есть таблица, используйте её ID")
    print()
    
    response = input("Создать новую таблицу? (y/n): ")
    if response.lower() in ['y', 'yes', 'да']:
        spreadsheet_id = create_spreadsheet()
        if spreadsheet_id:
            print(f"\n🎉 Таблица успешно создана!")
            print(f"📋 ID: {spreadsheet_id}")
            print(f"🔗 Ссылка: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
            print("\n📝 Следующие шаги:")
            print("1. Замените 'your_bot_token_here' в .env на ваш токен бота")
            print("2. Запустите: python test_connection.py")
            print("3. Если все тесты пройдены, запустите: python bot.py")
        else:
            print("❌ Не удалось создать таблицу")
    else:
        print("Операция отменена")

if __name__ == "__main__":
    main()

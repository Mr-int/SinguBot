#!/usr/bin/env python3
"""
Скрипт для исправления структуры существующей Google таблицы.
Используйте этот скрипт, если данные в таблице находятся в неправильных колонках.
"""

import os
from dotenv import load_dotenv
from sheets_handler import GoogleSheetsHandler

load_dotenv()

def fix_table_structure():
    """Исправляет структуру таблицы, перемещая данные в правильные колонки."""
    
    # Инициализация Google Sheets
    sheets_handler = GoogleSheetsHandler(
        credentials_path='credentials.json',
        spreadsheet_id=os.getenv('SPREADSHEET_ID')
    )
    
    try:
        # Получаем все данные из таблицы
        result = sheets_handler.service.spreadsheets().values().get(
            spreadsheetId=sheets_handler.spreadsheet_id,
            range='A:R'
        ).execute()
        
        values = result.get('values', [])
        print(f"Найдено {len(values)} строк в таблице")
        
        if len(values) < 2:
            print("Таблица пуста или содержит только заголовки")
            return
        
        # Обрабатываем каждую строку (пропускаем заголовки)
        for i, row in enumerate(values[1:], start=2):
            if len(row) < 18:
                # Дополняем строку до 18 колонок
                row += [''] * (18 - len(row))
            
            # Проверяем, есть ли данные о лидах в неправильных колонках
            # Ищем данные о лидах в колонках, где они не должны быть
            has_leads_data = False
            for col in range(4, 12):  # Колонки E-L
                if col < len(row) and row[col] and str(row[col]).isdigit():
                    # Если в колонке E-L есть числа, возможно это баллы в неправильном месте
                    has_leads_data = True
                    break
            
            if has_leads_data:
                print(f"Строка {i}: обнаружены данные в неправильных колонках")
                
                # Перемещаем данные в правильные колонки
                # Создаем новую структуру строки
                new_row = [''] * 18
                
                # Копируем основные данные
                for j in range(min(len(row), 18)):
                    new_row[j] = row[j]
                
                # Убеждаемся, что баллы находятся в колонке L (индекс 11)
                if len(new_row) > 11 and new_row[11] and str(new_row[11]).isdigit():
                    # Баллы уже в правильном месте
                    pass
                else:
                    # Ищем баллы в других колонках и перемещаем в L
                    for col in range(4, 12):
                        if col < len(new_row) and new_row[col] and str(new_row[col]).isdigit():
                            try:
                                points = int(new_row[col])
                                if 0 <= points <= 1000:  # Разумный диапазон баллов
                                    new_row[11] = str(points)  # Перемещаем в колонку L
                                    new_row[col] = ''  # Очищаем старую колонку
                                    print(f"  Перемещено {points} баллов в колонку L")
                                    break
                            except ValueError:
                                continue
                
                # Обновляем строку в таблице
                sheets_handler.service.spreadsheets().values().update(
                    spreadsheetId=sheets_handler.spreadsheet_id,
                    range=f'A{i}:R{i}',
                    valueInputOption='RAW',
                    body={'values': [new_row]}
                ).execute()
                print(f"  Строка {i} исправлена")
        
        print("Структура таблицы исправлена!")
        
    except Exception as e:
        print(f"Ошибка при исправлении таблицы: {e}")

if __name__ == "__main__":
    print("Скрипт для исправления структуры Google таблицы")
    print("Убедитесь, что у вас есть:")
    print("1. Файл .env с SPREADSHEET_ID")
    print("2. Файл credentials.json для Google Sheets API")
    print("3. Доступ к таблице для Service Account")
    print()
    
    response = input("Продолжить? (y/n): ")
    if response.lower() in ['y', 'yes', 'да']:
        fix_table_structure()
    else:
        print("Операция отменена")

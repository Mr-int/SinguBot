from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import List, Dict, Any
import os

class GoogleSheetsHandler:
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.spreadsheet_id = spreadsheet_id

    def append_row(self, values: List[Any]) -> None:
        """Добавляет новую строку в таблицу."""
        # Получаем текущие значения столбца A
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='A:A'
        ).execute()
        current_values = result.get('values', [])
        
        # Если есть существующие значения, используем первое значение из столбца A
        if current_values and len(current_values) > 0:
            values[0] = current_values[0][0] if current_values[0] else ''
        
        body = {
            'values': [values]
        }
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range='A:M',
            valueInputOption='RAW',
            body=body
        ).execute()

    def update_participant_row(self, participant_id: int, lead_data: Dict[str, Any]) -> None:
        """Обновляет существующую строку участника, добавляя нового лида."""
        # Получаем все значения из таблицы
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='A:M'
        ).execute()
        values = result.get('values', [])

        # Ищем строку с нужным participant_id
        for i, row in enumerate(values):
            if len(row) > 1 and str(row[1]) == str(participant_id):
                # Формируем данные для обновления, начиная со столбца B
                current_values = row[1:4]  # Копируем B, C, D столбцы
                
                # Добавляем нового лида в существующие данные
                if len(row) <= 4:  # Если это первый лид
                    current_values.extend([
                        lead_data['child_name'],  # E: ФИО лид
                        lead_data['age'],  # F: Возраст
                        lead_data['grade'],  # G: Класс
                        lead_data['telegram'],  # H: Ник в тг
                        lead_data['phone'],  # I: Номер телефона
                        lead_data['parent_name'],  # J: ФИО (родитель)
                        lead_data['parent_phone'],  # K: Номер телефона (родитель)
                        '0',  # L: Балл
                        'На проверке'  # M: Статус
                    ])
                else:  # Если уже есть лиды
                    # Добавляем нового лида через перенос строки
                    current_values.extend([
                        f"{row[4]}\n{lead_data['child_name']}",  # E: ФИО лид
                        f"{row[5]}\n{lead_data['age']}",  # F: Возраст
                        f"{row[6]}\n{lead_data['grade']}",  # G: Класс
                        f"{row[7]}\n{lead_data['telegram']}",  # H: Ник в тг
                        f"{row[8]}\n{lead_data['phone']}",  # I: Номер телефона
                        f"{row[9]}\n{lead_data['parent_name']}",  # J: ФИО (родитель)
                        f"{row[10]}\n{lead_data['parent_phone']}",  # K: Номер телефона (родитель)
                        row[11] if len(row) > 11 else '0',  # L: Балл
                        row[12] if len(row) > 12 else 'На проверке'  # M: Статус
                    ])
                
                # Обновляем строку, начиная со столбца B
                update_range = f'B{i+1}:M{i+1}'
                body = {
                    'values': [current_values]
                }
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=update_range,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                return

    def get_participant_points(self, participant_id: int) -> int:
        """Получает баллы участника из таблицы."""
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='B:L'
        ).execute()
        values = result.get('values', [])
        
        for row in values:
            if len(row) > 0 and str(row[0]) == str(participant_id):
                return int(row[10]) if len(row) > 10 else 0
        return 0

    def get_all_leads(self, participant_id: int) -> List[Dict[str, Any]]:
        """Получает все лиды участника из таблицы."""
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='A:M'
        ).execute()
        values = result.get('values', [])
        leads = []
        
        for row in values:
            if len(row) > 1 and str(row[1]) == str(participant_id):
                # Разделяем данные лидов по переносу строки
                child_names = row[4].split('\n') if len(row) > 4 and row[4] else []
                ages = row[5].split('\n') if len(row) > 5 and row[5] else []
                grades = row[6].split('\n') if len(row) > 6 and row[6] else []
                telegrams = row[7].split('\n') if len(row) > 7 and row[7] else []
                phones = row[8].split('\n') if len(row) > 8 and row[8] else []
                parent_names = row[9].split('\n') if len(row) > 9 and row[9] else []
                parent_phones = row[10].split('\n') if len(row) > 10 and row[10] else []
                
                # Определяем максимальное количество лидов
                max_leads = max(
                    len(child_names),
                    len(ages),
                    len(grades),
                    len(telegrams),
                    len(phones),
                    len(parent_names),
                    len(parent_phones)
                )
                
                # Создаем отдельный словарь для каждого лида
                for i in range(max_leads):
                    lead = {
                        'child_name': child_names[i] if i < len(child_names) else '',
                        'age': ages[i] if i < len(ages) else '',
                        'grade': grades[i] if i < len(grades) else '',
                        'telegram': telegrams[i] if i < len(telegrams) else '',
                        'phone': phones[i] if i < len(phones) else '',
                        'parent_name': parent_names[i] if i < len(parent_names) else '',
                        'parent_phone': parent_phones[i] if i < len(parent_phones) else '',
                        'status': row[12] if len(row) > 12 else 'На проверке'
                    }
                    leads.append(lead)
        return leads 
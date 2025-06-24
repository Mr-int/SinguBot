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

    def update_ids_in_sheet(self, participant_id: int, chat_id: int, telegram_id: int) -> None:
        """Находит участника по его ID (столбец B) и обновляет его chat_id (Q) и telegram_id (R)."""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='A:R'
            ).execute()
            values = result.get('values', [])
            
            for i, row in enumerate(values[1:], start=2):
                if len(row) > 1 and row[1] and int(row[1]) == participant_id:
                    
                    chat_id_needs_update = len(row) <= 16 or not row[16]
                    telegram_id_needs_update = len(row) <= 17 or not row[17]

                    if chat_id_needs_update or telegram_id_needs_update:
                        update_range = f'Q{i}:R{i}'
                        update_values = [
                            chat_id if chat_id_needs_update else row[16],
                            telegram_id if telegram_id_needs_update else row[17]
                        ]
                        body = {'values': [update_values]}
                        self.service.spreadsheets().values().update(
                            spreadsheetId=self.spreadsheet_id,
                            range=update_range,
                            valueInputOption='RAW',
                            body=body
                        ).execute()
                    return
        except Exception as e:
            print(f"Error updating IDs in sheet: {e}")

    def find_participant_by_telegram_id(self, telegram_id: int) -> list | None:
        """Ищет участника по telegram_id в столбце R."""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='A:R'
            ).execute()
            values = result.get('values', [])
            
            # Ищем со второй строки, чтобы пропустить заголовок
            for row in values[1:]:
                # Проверяем, что в строке есть столбец R и его значение совпадает
                if len(row) > 17 and row[17] and str(row[17]) == str(telegram_id):
                    return row
            return None
        except Exception as e:
            print(f"Error finding participant by telegram_id: {e}")
            return None

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
            range='A:R',
            valueInputOption='RAW',
            body=body
        ).execute()

    def update_participant_row(self, participant_id: int, lead_data: Dict[str, Any], chat_id: int) -> None:
        """Обновляет существующую строку участника, добавляя нового лида и chat_id."""
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='A:R'
        ).execute()
        values = result.get('values', [])

        for i, row in enumerate(values):
            if len(row) > 1 and str(row[1]) == str(participant_id):
                updated_row = row[:]
                while len(updated_row) < 18:
                    updated_row.append('')

                new_lead_values = [
                    lead_data['child_name'],
                    lead_data['age'],
                    lead_data['grade'],
                    lead_data['telegram'],
                    lead_data['phone'],
                    lead_data['parent_name'],
                    lead_data['parent_phone']
                ]

                if updated_row[4] == '':
                    for j, value in enumerate(new_lead_values):
                        updated_row[4+j] = value
                    if not updated_row[11]:
                        updated_row[11] = '0'
                else:
                    for j, value in enumerate(new_lead_values):
                        updated_row[4+j] = f"{updated_row[4+j]}\n{value}"
                
                if not updated_row[16]:
                    updated_row[16] = chat_id

                update_range = f'B{i+1}:R{i+1}'
                body = {
                    'values': [updated_row[1:]]
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
            range='A:R'
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
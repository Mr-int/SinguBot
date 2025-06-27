from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import List, Dict, Any


class GoogleSheetsHandler:
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.spreadsheet_id = spreadsheet_id

    def update_ids_in_sheet(self, participant_id: int, chat_id: int, telegram_id: int) -> None:
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='A:R'
            ).execute()
            values = result.get('values', [])

            for i, row in enumerate(values[1:], start=2):
                if len(row) > 1 and row[1] and int(row[1]) == participant_id:
                    row += [''] * (18 - len(row))  # Ensure at least 18 columns

                    chat_id_needs_update = not row[16]
                    telegram_id_needs_update = not row[17]

                    if chat_id_needs_update or telegram_id_needs_update:
                        update_values = [
                            [chat_id if chat_id_needs_update else row[16],
                             telegram_id if telegram_id_needs_update else row[17]]
                        ]
                        self.service.spreadsheets().values().update(
                            spreadsheetId=self.spreadsheet_id,
                            range=f'Q{i}:R{i}',
                            valueInputOption='RAW',
                            body={'values': update_values}
                        ).execute()
                    return
        except Exception as e:
            print(f"Error updating IDs in sheet: {e}")

    def find_participant_by_telegram_id(self, telegram_id: int) -> list | None:
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='A:R'
            ).execute()
            values = result.get('values', [])
            for row in values[1:]:
                if len(row) > 17 and row[17] and str(row[17]) == str(telegram_id):
                    return row
            return None
        except Exception as e:
            print(f"Error finding participant by telegram_id: {e}")
            return None

    def append_row(self, values: List[Any]) -> None:
        # Получаем все строки
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='A:R'
        ).execute()
        rows = result.get('values', [])
        row_num = len(rows) + 1
        # Гарантируем 17 элементов (B–R)
        if len(values) < 17:
            values += [''] * (17 - len(values))
        elif len(values) > 17:
            values = values[:17]
        # Обновляем диапазон B{row_num}:R{row_num}
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f'B{row_num}:R{row_num}',
            valueInputOption='RAW',
            body={'values': [values]}
        ).execute()

    def update_participant_row(self, participant_id: int, lead_data: Dict[str, Any], chat_id: int) -> None:
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='A:R'
            ).execute()
            values = result.get('values', [])

            for i, row in enumerate(values):
                if len(row) > 1 and str(row[1]) == str(participant_id):
                    updated_row = row[:]
                    updated_row += [''] * (18 - len(updated_row))

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
                            updated_row[4 + j] = value
                        if not updated_row[11]:
                            updated_row[11] = '0'
                    else:
                        for j, value in enumerate(new_lead_values):
                            updated_row[4 + j] = f"{updated_row[4 + j]}\n{value}"

                    if not updated_row[16]:
                        updated_row[16] = chat_id

                    # Формируем диапазоны без A и M
                    batch_body = {
                        'valueInputOption': 'RAW',
                        'data': [
                            {
                                'range': f'B{i+1}:L{i+1}',
                                'values': [updated_row[1:12]]
                            },
                            {
                                'range': f'N{i+1}:Q{i+1}',
                                'values': [updated_row[13:17]]
                            }
                        ]
                    }
                    self.service.spreadsheets().values().batchUpdate(
                        spreadsheetId=self.spreadsheet_id,
                        body=batch_body
                    ).execute()
                    return
        except Exception as e:
            print(f"Error updating participant row: {e}")

    def get_participant_points(self, participant_id: int) -> int:
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='B:L'
            ).execute()
            values = result.get('values', [])
            for row in values:
                if len(row) > 0 and str(row[0]) == str(participant_id):
                    return int(row[10]) if len(row) > 10 else 0
            return 0
        except Exception as e:
            print(f"Error getting participant points: {e}")
            return 0

    def get_all_leads(self, participant_id: int) -> List[Dict[str, Any]]:
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='A:R'
            ).execute()
            values = result.get('values', [])
            leads = []
            for row in values:
                if len(row) > 1 and str(row[1]) == str(participant_id):
                    child_names = row[4].split('\n') if len(row) > 4 and row[4] else []
                    ages = row[5].split('\n') if len(row) > 5 and row[5] else []
                    grades = row[6].split('\n') if len(row) > 6 and row[6] else []
                    telegrams = row[7].split('\n') if len(row) > 7 and row[7] else []
                    phones = row[8].split('\n') if len(row) > 8 and row[8] else []
                    parent_names = row[9].split('\n') if len(row) > 9 and row[9] else []
                    parent_phones = row[10].split('\n') if len(row) > 10 and row[10] else []
                    max_leads = max(
                        len(child_names), len(ages), len(grades),
                        len(telegrams), len(phones),
                        len(parent_names), len(parent_phones)
                    )
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
        except Exception as e:
            print(f"Error getting leads: {e}")
            return []

    def get_max_id(self) -> int:
        """Возвращает максимальный ID участника из столбца B."""
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='B:B'
        ).execute()
        values = result.get('values', [])
        max_id = 0
        for row in values[1:]:
            try:
                val = int(row[0])
                if val > max_id:
                    max_id = val
            except Exception:
                continue
        return max_id

    def add_participant(self, participant_id: int, full_name: str, course: int, chat_id: int = '', telegram_id: int = '') -> None:
        """Добавляет нового участника в Google-таблицу."""
        row = [
            participant_id,      # B
            full_name,           # C
            course,              # D
        ] + [''] * 8 + [        # E–L (8 пустых)
            '',                 # M — пустой
        ] + [''] * 3 + [        # N–P (3 пустых)
            chat_id,            # Q
            telegram_id         # R
        ]
        self.append_row(row)

    def add_lead(self, participant_id: int, lead_data: dict) -> None:
        """Добавляет нового лида к участнику в Google-таблице."""
        # Получаем все строки
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='A:R'
        ).execute()
        values = result.get('values', [])
        for i, row in enumerate(values):
            if len(row) > 1 and str(row[1]) == str(participant_id):
                # Обновляем данные по лидам (E–K: 5–11)
                for idx, key in enumerate(['child_name', 'age', 'grade', 'telegram', 'phone', 'parent_name', 'parent_phone']):
                    col = 4 + idx  # E=4, F=5, ..., K=10
                    if len(row) <= col:
                        row += [''] * (col - len(row) + 1)
                    if row[col]:
                        row[col] += f"\n{lead_data.get(key, '')}"
                    else:
                        row[col] = str(lead_data.get(key, ''))
                # Обновляем строку в таблице
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'A{i+1}:R{i+1}',
                    valueInputOption='RAW',
                    body={'values': [row]}
                ).execute()
                return


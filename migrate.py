import sqlite3
import os

DB_FILE = 'ambassador.db'

def migrate():
    """
    Adds the chat_id column to the participants table in the SQLite database
    if it doesn't already exist.
    """
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found. Nothing to migrate.")
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Check if the column already exists
        cursor.execute("PRAGMA table_info(participants)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'chat_id' not in columns:
            # Add the chat_id column. It can be NULL for existing users.
            cursor.execute('ALTER TABLE participants ADD COLUMN chat_id INTEGER')
            print("Column 'chat_id' added to 'participants' table successfully.")
        else:
            print("Column 'chat_id' already exists.")

        conn.commit()
        conn.close()

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    migrate()

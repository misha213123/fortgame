import sqlite3
import os

def initialize_database():
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        city TEXT NOT NULL,
        coins INTEGER DEFAULT 0,
        purchases TEXT DEFAULT '',
        correct_answers INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fort_boyard (
        user_id INTEGER PRIMARY KEY,
        stage INTEGER DEFAULT 0,
        coins INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sequence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()

def save_user_data(user_id, first_name, last_name, phone_number, city):
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, first_name, last_name, phone_number, city) VALUES (?, ?, ?, ?, ?)",
                   (user_id, first_name, last_name, phone_number, city))
    conn.commit()
    conn.close()

def load_user_profile(user_id):
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, last_name, phone_number, city, coins, purchases, correct_answers FROM users WHERE user_id = ?", (user_id,))
    profile_data = cursor.fetchone()
    if profile_data:
        cursor.execute("SELECT stage, coins FROM fort_boyard WHERE user_id = ?", (user_id,))
        fort_boyard_data = cursor.fetchone()
        if fort_boyard_data:
            profile_data = profile_data[:5] + (fort_boyard_data[0],) + profile_data[5:]
    conn.close()
    return profile_data



def update_user_profile(user_id, coins=None, purchases=None, correct_answers=None):
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    if coins is not None:
        cursor.execute("UPDATE users SET coins = ? WHERE user_id = ?", (coins, user_id))
    if purchases is not None:
        cursor.execute("UPDATE users SET purchases = ? WHERE user_id = ?", (purchases, user_id))
    if correct_answers is not None:
        cursor.execute("UPDATE users SET correct_answers = ? WHERE user_id = ?", (correct_answers, user_id))
    conn.commit()
    conn.close()

def save_message_to_sequence(user_id, message):
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sequence (user_id, message) VALUES (?, ?)", (user_id, message))
    conn.commit()
    conn.close()

def load_pending_messages():
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, message FROM sequence ORDER BY timestamp ASC")
    pending_messages = cursor.fetchall()
    conn.close()
    return pending_messages

def delete_message_from_sequence(user_id):
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sequence WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# Initialize the database on import
initialize_database()

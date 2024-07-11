import sqlite3
import os
from telegram.ext import Application

def send_notification(message):
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    application = Application.builder().token(TOKEN).build()
    for user_id, in users:
        application.bot.send_message(chat_id=user_id, text=message)

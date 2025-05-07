# utils/database.py

import sqlite3
from datetime import datetime, timedelta

DB_NAME = "learning_data.db"

def initialize_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            topic TEXT NOT NULL,
            last_reviewed DATE,
            memory_level INTEGER DEFAULT 100
        )
    """)
    conn.commit()
    conn.close()

def add_topic(user, topic):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO topics (user, topic, last_reviewed) VALUES (?, ?, ?)", 
                   (user, topic, datetime.today().strftime('%Y-%m-%d')))
    conn.commit()
    conn.close()

def mark_reviewed(user, topic):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE topics
        SET last_reviewed = ?, memory_level = memory_level - 10
        WHERE user = ? AND topic = ?
    """, (datetime.today().strftime('%Y-%m-%d'), user, topic))
    conn.commit()
    conn.close()

def get_review_schedule(user):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT topic, last_reviewed, memory_level FROM topics WHERE user = ?", (user,))
    rows = cursor.fetchall()
    conn.close()

    schedule = {"Today": [], "Tomorrow": [], "Later": []}
    today = datetime.today().date()

    for topic, last_reviewed_str, memory in rows:
        last_reviewed = datetime.strptime(last_reviewed_str, "%Y-%m-%d").date() if last_reviewed_str else today
        days_since_review = (today - last_reviewed).days

        if memory <= 50:
            label = "Today"
        elif memory <= 75:
            label = "Tomorrow"
        else:
            label = "Later"

        schedule[label].append(topic)

    return schedule

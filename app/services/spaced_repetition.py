import sqlite3
from datetime import datetime, timedelta

def get_connection():
    return sqlite3.connect('data/database.db', check_same_thread=False)

def get_review_schedule(user_name):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT topic, timestamp FROM user_data
        WHERE user_name = ?
        ORDER BY timestamp DESC
    """, (user_name,))
    rows = cursor.fetchall()
    conn.close()

    schedule = {"Today": [], "Tomorrow": [], "Later": []}
    today = datetime.now().date()

    for topic, ts in rows:
        review_date = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S').date()
        days_since = (today - review_date).days

        if days_since >= 7:
            schedule["Today"].append(topic)
        elif days_since >= 3:
            schedule["Tomorrow"].append(topic)
        else:
            schedule["Later"].append(topic)

    return schedule

def mark_reviewed(user_name, topic):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_data
        SET timestamp = CURRENT_TIMESTAMP
        WHERE user_name = ? AND topic = ?
    """, (user_name, topic))
    conn.commit()
    conn.close()

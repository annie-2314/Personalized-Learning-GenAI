import sqlite3
import os
from datetime import datetime, timedelta

def initialize_db():
    try:
        if not os.path.exists('data'):
            os.makedirs('data')
            print("DEBUG: Created 'data' directory")
        db_path = os.path.join("data", "database.db")
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                user_name TEXT,
                topic_name TEXT,
                memory_level INTEGER,
                last_reviewed TEXT,
                next_review TEXT,
                PRIMARY KEY (user_name, topic_name)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS streaks (
                user_name TEXT PRIMARY KEY,
                streak_count INTEGER,
                last_activity_date TEXT
            )
        """)
        conn.commit()
        print(f"DEBUG: Initialized database at {db_path}")
        # Verify tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"DEBUG: Tables in database: {tables}")
    except Exception as e:
        print(f"DEBUG: Error initializing database: {e}")
    finally:
        conn.close()

def add_topic(user_name, topic_name):
    try:
        conn = sqlite3.connect("data/database.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO topics (user_name, topic_name, memory_level, last_reviewed, next_review)
            VALUES (?, ?, ?, ?, ?)
        """, (user_name, topic_name.lower(), 100, datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d')))
        update_streak(user_name)
        conn.commit()
        print(f"DEBUG: Added topic '{topic_name}' for user '{user_name}'")
    except Exception as e:
        print(f"DEBUG: Error adding topic: {e}")
    finally:
        conn.close()

def mark_reviewed(user_name, topic_name):
    try:
        conn = sqlite3.connect("data/database.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT memory_level FROM topics WHERE user_name = ? AND topic_name = ?", (user_name, topic_name.lower()))
        result = cursor.fetchone()
        if result:
            memory_level = result[0]
            new_memory_level = max(0, memory_level - 20)
            days_to_next_review = {100: 1, 80: 2, 60: 4, 40: 7, 20: 14, 0: 30}.get(new_memory_level, 30)
            next_review = (datetime.now() + timedelta(days=days_to_next_review)).strftime('%Y-%m-%d')
            cursor.execute("""
                UPDATE topics
                SET memory_level = ?, last_reviewed = ?, next_review = ?
                WHERE user_name = ? AND topic_name = ?
            """, (new_memory_level, datetime.now().strftime('%Y-%m-%d'), next_review, user_name, topic_name.lower()))
            update_streak(user_name)
            conn.commit()
            print(f"DEBUG: Marked '{topic_name}' as reviewed for user '{user_name}'")
    except Exception as e:
        print(f"DEBUG: Error marking topic reviewed: {e}")
    finally:
        conn.close()

def update_streak(user_name):
    try:
        today = datetime.now().date().strftime('%Y-%m-%d')
        conn = sqlite3.connect("data/database.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT streak_count, last_activity_date FROM streaks WHERE user_name = ?", (user_name,))
        result = cursor.fetchone()
        if result:
            streak, last_date = result
            try:
                last_date = datetime.strptime(last_date, '%Y-%m-%d').date()
                if last_date == datetime.now().date():
                    return
                elif last_date == (datetime.now().date() - timedelta(days=1)):
                    streak += 1
                else:
                    streak = 1
            except ValueError:
                streak = 1
            cursor.execute("UPDATE streaks SET streak_count = ?, last_activity_date = ? WHERE user_name = ?",
                          (streak, today, user_name))
        else:
            cursor.execute("INSERT INTO streaks (user_name, streak_count, last_activity_date) VALUES (?, ?, ?)",
                          (user_name, 1, today))
        conn.commit()
        print(f"DEBUG: Updated streak for user '{user_name}'")
    except Exception as e:
        print(f"DEBUG: Error updating streak: {e}")
    finally:
        conn.close()

def get_streak(user_name):
    try:
        conn = sqlite3.connect("data/database.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT streak_count FROM streaks WHERE user_name = ?", (user_name,))
        result = cursor.fetchone()
        conn.close()
        print(f"DEBUG: Fetched streak for user '{user_name}': {result[0] if result else 0}")
        return result[0] if result else 0
    except Exception as e:
        print(f"DEBUG: Error getting streak: {e}")
        return 0

def get_all_topics(user_name):
    try:
        conn = sqlite3.connect("data/database.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT user_name, topic_name, memory_level, last_reviewed, next_review FROM topics WHERE user_name = ?", (user_name,))
        topics = cursor.fetchall()
        conn.close()
        print(f"DEBUG: Fetched {len(topics)} topics for user '{user_name}': {topics}")
        return topics
    except Exception as e:
        print(f"DEBUG: Error getting topics: {e}")
        return []

def get_review_schedule(user_name):
    try:
        conn = sqlite3.connect("data/database.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT topic_name, next_review FROM topics WHERE user_name = ?", (user_name,))
        topics = cursor.fetchall()
        conn.close()
        schedule = {"Today": [], "Tomorrow": [], "Later": []}
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        for topic, next_review in topics:
            try:
                next_review_date = datetime.strptime(next_review, '%Y-%m-%d').date()
                if next_review_date <= today:
                    schedule["Today"].append(topic)
                elif next_review_date == tomorrow:
                    schedule["Tomorrow"].append(topic)
                else:
                    schedule["Later"].append(topic)
            except ValueError:
                schedule["Later"].append(topic)  # Handle invalid dates
        print(f"DEBUG: Schedule for user '{user_name}': {schedule}")
        return schedule
    except Exception as e:
        print(f"DEBUG: Error getting schedule: {e}")
        return {"Today": [], "Tomorrow": [], "Later": []}
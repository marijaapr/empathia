import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.getenv('DATABASE_PATH', 'empathia.db')


def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            language TEXT DEFAULT 'en',
            preferred_persona TEXT DEFAULT 'supportive_friend',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            persona TEXT DEFAULT 'supportive_friend',
            language TEXT DEFAULT 'en',
            mood_detected TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Mood entries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mood_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            mood TEXT NOT NULL,
            intensity INTEGER DEFAULT 5,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()


def get_or_create_user(username='default_user'):
    """Get or create a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
        conn.commit()
        user_id = cursor.lastrowid
    else:
        user_id = user['id']
    
    conn.close()
    return user_id


def add_message(user_id, role, content, persona='supportive_friend', language='en', mood_detected=None):
    """Add a message to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO messages (user_id, role, content, persona, language, mood_detected)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, role, content, persona, language, mood_detected))
    
    conn.commit()
    message_id = cursor.lastrowid
    conn.close()
    return message_id


def get_user_messages(user_id, limit=50):
    """Get recent messages for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM messages WHERE user_id = ?
        ORDER BY created_at DESC LIMIT ?
    ''', (user_id, limit))
    
    messages = cursor.fetchall()
    conn.close()
    return messages


def add_mood_entry(user_id, mood, intensity=5, notes=None):
    """Add a mood entry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO mood_entries (user_id, mood, intensity, notes)
        VALUES (?, ?, ?, ?)
    ''', (user_id, mood, intensity, notes))
    
    conn.commit()
    entry_id = cursor.lastrowid
    conn.close()
    return entry_id


def get_mood_history(user_id, days=30):
    """Get mood history for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DATE(created_at) as date, mood, COUNT(*) as count
        FROM mood_entries
        WHERE user_id = ? AND created_at >= datetime('now', '-' || ? || ' days')
        GROUP BY DATE(created_at), mood
        ORDER BY date DESC
    ''', (user_id, days))
    
    entries = cursor.fetchall()
    conn.close()
    return entries


def get_weekly_mood_summary(user_id):
    """Get weekly mood summary for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT mood, COUNT(*) as count, AVG(intensity) as avg_intensity
        FROM mood_entries
        WHERE user_id = ? AND created_at >= datetime('now', '-7 days')
        GROUP BY mood
        ORDER BY count DESC
    ''', (user_id,))
    
    summary = cursor.fetchall()
    conn.close()
    return summary


def update_user_settings(user_id, language=None, persona=None):
    """Update user settings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if language:
        cursor.execute('UPDATE users SET language = ? WHERE id = ?', (language, user_id))
    if persona:
        cursor.execute('UPDATE users SET preferred_persona = ? WHERE id = ?', (persona, user_id))
    
    cursor.execute('UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()


def get_user_settings(user_id):
    """Get user settings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT language, preferred_persona FROM users WHERE id = ?', (user_id,))
    settings = cursor.fetchone()
    conn.close()
    return dict(settings) if settings else {}

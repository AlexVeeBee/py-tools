import sqlite3
import json
import os
from datetime import datetime

class DBManager:
    _db_path = "prompt_builder.db"  # Default

    @classmethod
    def set_db_path(cls, path):
        """Sets the active database path and initializes tables if needed."""
        cls._db_path = path
        cls.init_db()

    @classmethod
    def get_db_path(cls):
        return cls._db_path

    @staticmethod
    def _get_connection():
        # Ensure directory exists if it's a path
        folder = os.path.dirname(DBManager._db_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
            
        conn = sqlite3.connect(DBManager._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def init_db():
        """Creates the necessary tables if they don't exist."""
        conn = DBManager._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def save_prompt(name, data_dict):
        """Saves or Updates a prompt configuration."""
        json_data = json.dumps(data_dict)
        conn = DBManager._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO prompts (name, data, updated_at) 
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    data=excluded.data,
                    updated_at=excluded.updated_at
            """, (name, json_data, datetime.now()))
            conn.commit()
            return True, "Saved successfully."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_all_prompts():
        """Returns list of (id, name, updated_at)."""
        conn = DBManager._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name, updated_at FROM prompts ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            return rows
        except sqlite3.Error:
            return []
        finally:
            conn.close()

    @staticmethod
    def load_prompt(name):
        """Returns the dictionary data for a specific prompt name."""
        conn = DBManager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM prompts WHERE name = ?", (name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row['data'])
        return None
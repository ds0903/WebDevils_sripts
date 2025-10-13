import sqlite3
from pathlib import Path
from datetime import datetime
import json


class Database:
    def __init__(self, db_path='data/threads_bot.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = None
        self.init_database()
    
    def get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                max_comments_per_run INTEGER DEFAULT 5,
                enabled BOOLEAN DEFAULT 1,
                headless BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comment_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword_id INTEGER NOT NULL,
                template_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                post_id TEXT NOT NULL,
                post_link TEXT,
                keyword TEXT,
                comment_text TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                UNIQUE(account_id, post_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        default_settings = [
            ('delay_between_comments_min', '10', 'Мінімальна затримка між коментарями (секунди)'),
            ('delay_between_comments_max', '30', 'Максимальна затримка між коментарями (секунди)'),
            ('delay_between_accounts_min', '60', 'Мінімальна затримка між акаунтами (секунди)'),
            ('delay_between_accounts_max', '120', 'Максимальна затримка між акаунтами (секунди)'),
            ('delay_between_posts_min', '5', 'Мінімальна затримка між постами (секунди)'),
            ('delay_between_posts_max', '15', 'Максимальна затримка між постами (секунди)'),
            ('run_interval_minutes', '10', 'Інтервал запуску бота (хвилини)'),
            ('max_post_age_hours', '24', 'Макс. вік поста для коментування (годин, 0=без обмежень)'),
        ]
        
        for key, value, desc in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value, description)
                VALUES (?, ?, ?)
            ''', (key, value, desc))
        
        conn.commit()
    
    def get_all_accounts(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts ORDER BY id')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_account(self, account_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def create_account(self, username, password, max_comments=5, enabled=True, headless=False):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (username, password, max_comments_per_run, enabled, headless)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, password, max_comments, enabled, headless))
        conn.commit()
        return cursor.lastrowid
    
    def update_account(self, account_id, username=None, password=None, max_comments=None, enabled=None, headless=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if username is not None:
            updates.append('username = ?')
            params.append(username)
        if password is not None:
            updates.append('password = ?')
            params.append(password)
        if max_comments is not None:
            updates.append('max_comments_per_run = ?')
            params.append(max_comments)
        if enabled is not None:
            updates.append('enabled = ?')
            params.append(enabled)
        if headless is not None:
            updates.append('headless = ?')
            params.append(headless)
        
        if updates:
            params.append(account_id)
            cursor.execute(f'''
                UPDATE accounts SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
            conn.commit()
    
    def delete_account(self, account_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
        conn.commit()
    
    def get_all_keywords(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM keywords ORDER BY id')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_keyword(self, keyword_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM keywords WHERE id = ?', (keyword_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def create_keyword(self, keyword, enabled=True):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO keywords (keyword, enabled)
            VALUES (?, ?)
        ''', (keyword, enabled))
        conn.commit()
        return cursor.lastrowid
    
    def update_keyword(self, keyword_id, keyword=None, enabled=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if keyword is not None:
            updates.append('keyword = ?')
            params.append(keyword)
        if enabled is not None:
            updates.append('enabled = ?')
            params.append(enabled)
        
        if updates:
            params.append(keyword_id)
            cursor.execute(f'''
                UPDATE keywords SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
            conn.commit()
    
    def delete_keyword(self, keyword_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM keywords WHERE id = ?', (keyword_id,))
        conn.commit()
    
    def get_templates_for_keyword(self, keyword_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM comment_templates WHERE keyword_id = ?', (keyword_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def create_template(self, keyword_id, template_text):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO comment_templates (keyword_id, template_text)
            VALUES (?, ?)
        ''', (keyword_id, template_text))
        conn.commit()
        return cursor.lastrowid
    
    def delete_template(self, template_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM comment_templates WHERE id = ?', (template_id,))
        conn.commit()
    
    def add_comment_history(self, account_id, post_id, post_link, keyword, comment_text, status, error_message=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO comment_history (account_id, post_id, post_link, keyword, comment_text, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (account_id, post_id, post_link, keyword, comment_text, status, error_message))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def is_post_commented(self, account_id, post_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM comment_history
            WHERE account_id = ? AND post_id = ?
        ''', (account_id, post_id))
        return cursor.fetchone()['count'] > 0
    
    def get_comment_history(self, limit=100):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT h.*, a.username
            FROM comment_history h
            JOIN accounts a ON h.account_id = a.id
            ORDER BY h.created_at DESC
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error
            FROM comment_history
        ''')
        
        return dict(cursor.fetchone())
    
    def get_all_settings(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM settings ORDER BY key')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_setting(self, key):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row['value'] if row else None
    
    def update_setting(self, key, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE settings SET value = ?
            WHERE key = ?
        ''', (value, key))
        conn.commit()
    
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None


if __name__ == '__main__':
    db = Database()
    print("✅ База даних ініціалізована")

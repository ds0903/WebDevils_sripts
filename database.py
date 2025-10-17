import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self):
        self.connection_pool = None
        self.init_pool()
        self.init_database()
    
    def init_pool(self):
        """Ініціалізація пулу з'єднань з PostgreSQL"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'threads_bot'),
                user=os.getenv('DB_USER', 'danil'),
                password=os.getenv('DB_PASSWORD', '')
            )
        except Exception as e:
            print(f"❌ Помилка підключення до PostgreSQL: {e}")
            raise
    
    def get_connection(self):
        """Отримати з'єднання з пулу"""
        if self.connection_pool:
            return self.connection_pool.getconn()
        raise Exception("Connection pool is not initialized")
    
    def return_connection(self, conn):
        """Повернути з'єднання в пул"""
        if self.connection_pool:
            self.connection_pool.putconn(conn)
    
    def init_database(self):
        """Створення таблиць бази даних"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Таблиця акаунтів
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    max_comments_per_run INTEGER DEFAULT 5,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Видаляємо колонку headless якщо вона існує
            try:
                cursor.execute('''
                    ALTER TABLE accounts DROP COLUMN IF EXISTS headless
                ''')
            except:
                pass
            
            # Таблиця ключових слів
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS keywords (
                    id SERIAL PRIMARY KEY,
                    keyword VARCHAR(255) UNIQUE NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    should_follow BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Додаємо колонку should_follow якщо її немає (для існуючих БД)
            try:
                cursor.execute('''
                    ALTER TABLE keywords ADD COLUMN IF NOT EXISTS should_follow BOOLEAN DEFAULT FALSE
                ''')
            except:
                pass
            
            # Таблиця шаблонів коментарів
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comment_templates (
                    id SERIAL PRIMARY KEY,
                    keyword_id INTEGER NOT NULL,
                    template_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
                )
            ''')
            
            # Таблиця історії коментарів
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comment_history (
                    id SERIAL PRIMARY KEY,
                    account_id INTEGER NOT NULL,
                    post_id VARCHAR(255) NOT NULL,
                    post_link TEXT,
                    keyword VARCHAR(255),
                    comment_text TEXT,
                    status VARCHAR(50) NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                    UNIQUE(account_id, post_id)
                )
            ''')
            
            # Таблиця налаштувань
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(255) UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Додаємо дефолтні налаштування
            default_settings = [
                ('delay_between_comments_min', '10', 'Мінімальна затримка між коментарями (секунди)'),
                ('delay_between_comments_max', '30', 'Максимальна затримка між коментарями (секунди)'),
                ('delay_between_accounts_min', '60', 'Мінімальна затримка між акаунтами (секунди)'),
                ('delay_between_accounts_max', '120', 'Максимальна затримка між акаунтами (секунди)'),
                ('delay_between_posts_min', '5', 'Мінімальна затримка між постами (секунди)'),
                ('delay_between_posts_max', '15', 'Максимальна затримка між постами (секунди)'),
                ('run_interval_minutes', '10', 'Інтервал запуску бота (хвилини)'),
                ('max_post_age_hours', '24', 'Макс. вік поста для коментування (годин, 0=без обмежень)'),
                ('global_headless_mode', 'false', 'Глобальний headless режим (без вікна браузера)'),
            ]
            
            for key, value, desc in default_settings:
                cursor.execute('''
                    INSERT INTO settings (key, value, description)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (key) DO NOTHING
                ''', (key, value, desc))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Помилка створення таблиць: {e}")
            raise
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def get_all_accounts(self):
        """Отримати всі акаунти"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM accounts ORDER BY id')
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def get_account(self, account_id):
        """Отримати акаунт за ID"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM accounts WHERE id = %s', (account_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def create_account(self, username, password, max_comments=5, enabled=True):
        """Створити новий акаунт"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO accounts (username, password, max_comments_per_run, enabled)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            ''', (username, password, max_comments, enabled))
            account_id = cursor.fetchone()[0]
            conn.commit()
            return account_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def update_account(self, account_id, username=None, password=None, max_comments=None, enabled=None):
        """Оновити дані акаунта"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if username is not None:
                updates.append('username = %s')
                params.append(username)
            if password is not None:
                updates.append('password = %s')
                params.append(password)
            if max_comments is not None:
                updates.append('max_comments_per_run = %s')
                params.append(max_comments)
            if enabled is not None:
                updates.append('enabled = %s')
                params.append(enabled)
            
            if updates:
                params.append(account_id)
                query = f"UPDATE accounts SET {', '.join(updates)} WHERE id = %s"
                cursor.execute(query, params)
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def delete_account(self, account_id):
        """Видалити акаунт"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM accounts WHERE id = %s', (account_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def get_all_keywords(self):
        """Отримати всі ключові слова"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM keywords ORDER BY id')
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def get_keyword(self, keyword_id):
        """Отримати ключове слово за ID"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM keywords WHERE id = %s', (keyword_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def add_keyword(self, keyword, enabled=True, should_follow=False):
        """Створити нове ключове слово (alias для create_keyword)"""
        return self.create_keyword(keyword, enabled, should_follow)
    
    def create_keyword(self, keyword, enabled=True, should_follow=False):
        """Створити нове ключове слово"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO keywords (keyword, enabled, should_follow)
                VALUES (%s, %s, %s)
                RETURNING id
            ''', (keyword, enabled, should_follow))
            keyword_id = cursor.fetchone()[0]
            conn.commit()
            return keyword_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def toggle_keyword(self, keyword_id):
        """Переключити стан enabled для ключового слова"""
        keyword = self.get_keyword(keyword_id)
        if keyword:
            self.update_keyword(keyword_id, enabled=not keyword['enabled'])
    
    def toggle_keyword_follow(self, keyword_id):
        """Переключити стан should_follow для ключового слова"""
        keyword = self.get_keyword(keyword_id)
        if keyword:
            self.update_keyword(keyword_id, should_follow=not keyword.get('should_follow', False))
    
    def get_keyword_by_id(self, keyword_id):
        """Alias для get_keyword"""
        return self.get_keyword(keyword_id)
    
    def add_template(self, keyword_id, template_text):
        """Alias для create_template"""
        return self.create_template(keyword_id, template_text)
    
    def update_keyword(self, keyword_id, keyword=None, enabled=None, should_follow=None):
        """Оновити ключове слово"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if keyword is not None:
                updates.append('keyword = %s')
                params.append(keyword)
            if enabled is not None:
                updates.append('enabled = %s')
                params.append(enabled)
            if should_follow is not None:
                updates.append('should_follow = %s')
                params.append(should_follow)
            
            if updates:
                params.append(keyword_id)
                query = f"UPDATE keywords SET {', '.join(updates)} WHERE id = %s"
                cursor.execute(query, params)
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def delete_keyword(self, keyword_id):
        """Видалити ключове слово"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM keywords WHERE id = %s', (keyword_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def get_templates_for_keyword(self, keyword_id):
        """Отримати всі шаблони для ключового слова"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM comment_templates WHERE keyword_id = %s', (keyword_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def create_template(self, keyword_id, template_text):
        """Створити новий шаблон коментаря"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO comment_templates (keyword_id, template_text)
                VALUES (%s, %s)
                RETURNING id
            ''', (keyword_id, template_text))
            template_id = cursor.fetchone()[0]
            conn.commit()
            return template_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def delete_template(self, template_id):
        """Видалити шаблон коментаря"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM comment_templates WHERE id = %s', (template_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def add_comment_history(self, account_id, post_id, post_link, keyword, comment_text, status, error_message=None):
        """Додати запис в історію коментарів"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO comment_history (account_id, post_id, post_link, keyword, comment_text, status, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (account_id, post_id, post_link, keyword, comment_text, status, error_message))
            history_id = cursor.fetchone()[0]
            conn.commit()
            return history_id
        except psycopg2.IntegrityError:
            conn.rollback()
            return None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def is_post_commented(self, account_id, post_id):
        """Перевірити, чи був пост вже прокоментований цим акаунтом"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as count FROM comment_history
                WHERE account_id = %s AND post_id = %s
            ''', (account_id, post_id))
            count = cursor.fetchone()[0]
            return count > 0
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def get_comment_history(self, limit=100):
        """Отримати історію коментарів"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT h.*, a.username
                FROM comment_history h
                JOIN accounts a ON h.account_id = a.id
                ORDER BY h.created_at DESC
                LIMIT %s
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def get_statistics(self):
        """Отримати статистику коментарів"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error
                FROM comment_history
            ''')
            return dict(cursor.fetchone())
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def get_all_settings(self):
        """Отримати всі налаштування"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM settings ORDER BY key')
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def get_setting(self, key):
        """Отримати значення налаштування"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = %s', (key,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def update_setting(self, key, value):
        """Оновити значення налаштування"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE settings SET value = %s
                WHERE key = %s
            ''', (value, key))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            self.return_connection(conn)
    
    def close(self):
        """Закрити всі з'єднання"""
        if self.connection_pool:
            self.connection_pool.closeall()
            print("✅ З'єднання з базою даних закрито")


if __name__ == '__main__':
    try:
        db = Database()
        print("✅ База даних PostgreSQL ініціалізована")
    except Exception as e:
        print(f"❌ Помилка: {e}")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import json
import time
import random
from datetime import datetime
from pathlib import Path
import schedule
import logging
import pickle

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ThreadsSeleniumBot:
    def __init__(self, config_dir='config', data_dir='data'):
        self.config_dir = Path(config_dir)
        self.data_dir = Path(data_dir)
        self.sessions_dir = self.data_dir / 'sessions'
        
        self.data_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
        
        self.accounts = self.load_json(self.config_dir / 'accounts.json')
        self.keywords = self.load_json(self.config_dir / 'keywords.json')
        self.last_seen = self.load_json(self.data_dir / 'last_seen.json', default={})
        self.logs = self.load_json(self.data_dir / 'logs.json', default=[])
        
        self.driver = None
        self.current_account = None
    
    def load_json(self, path, default=None):
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default if default is not None else {}
    
    def save_json(self, path, data):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def init_driver(self, headless=False):
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def save_session(self, account_id):
        session_file = self.sessions_dir / f"{account_id}_session.pkl"
        cookies = self.driver.get_cookies()
        with open(session_file, 'wb') as f:
            pickle.dump(cookies, f)
        logger.info(f"Сесія збережена для {account_id}")
    
    def load_session(self, account_id):
        session_file = self.sessions_dir / f"{account_id}_session.pkl"
        if not session_file.exists():
            return False
        
        try:
            with open(session_file, 'rb') as f:
                cookies = pickle.load(f)
            
            self.driver.get('https://www.threads.net')
            time.sleep(2)
            
            for cookie in cookies:
                if 'expiry' in cookie:
                    cookie['expiry'] = int(cookie['expiry'])
                self.driver.add_cookie(cookie)
            
            self.driver.refresh()
            time.sleep(3)
            
            if self.is_logged_in():
                logger.info(f"Сесія завантажена для {account_id}")
                return True
            
        except Exception as e:
            logger.error(f"Помилка завантаження сесії: {e}")
        
        return False
    
    def is_logged_in(self):
        try:
            self.driver.find_element(By.XPATH, "//input[@placeholder='Search']")
            return True
        except:
            return False
    
    def login(self, account_id):
        account = self.accounts['accounts'][account_id]
        username = account.get('username')
        password = account.get('password')
        
        if not username or not password:
            logger.error(f"Немає логіна/паролю для {account_id}")
            return False
        
        if self.load_session(account_id):
            return True
        
        logger.info(f"Вхід в акаунт {account_id}")
        
        try:
            self.driver.get('https://www.threads.net/login')
            time.sleep(random.uniform(3, 5))
            
            username_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='username']"))
            )
            username_input.send_keys(username)
            time.sleep(random.uniform(0.5, 1))
            
            password_input = self.driver.find_element(By.XPATH, "//input[@name='password']")
            password_input.send_keys(password)
            time.sleep(random.uniform(0.5, 1))
            
            password_input.send_keys(Keys.RETURN)
            
            time.sleep(5)
            
            if self.is_logged_in():
                logger.info("✓ Вхід виконано успішно")
                self.save_session(account_id)
                return True
            else:
                logger.error("✗ Не вдалося увійти")
                return False
                
        except Exception as e:
            logger.error(f"Помилка входу: {e}")
            return False
    
    def search_keyword(self, keyword):
        try:
            logger.info(f"Пошук за ключовим словом: {keyword}")
            
            search_url = f"https://www.threads.net/search?q={keyword}&serp_type=default"
            self.driver.get(search_url)
            time.sleep(random.uniform(3, 5))
            
            self.scroll_to_load_posts()
            
            posts = self.extract_posts()
            logger.info(f"Знайдено {len(posts)} постів")
            return posts
            
        except Exception as e:
            logger.error(f"Помилка пошуку: {e}")
            return []
    
    def scroll_to_load_posts(self, scrolls=3):
        for i in range(scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 3))
    
    def extract_posts(self):
        posts = []
        try:
            post_elements = self.driver.find_elements(By.XPATH, "//article")
            
            for element in post_elements:
                try:
                    post_id = element.get_attribute('data-post-id') or str(time.time())
                    
                    try:
                        text_element = element.find_element(By.XPATH, ".//div[contains(@class, 'x1lliihq')]")
                        text = text_element.text
                    except:
                        text = ""
                    
                    try:
                        time_element = element.find_element(By.XPATH, ".//time")
                        timestamp = time_element.get_attribute('datetime')
                    except:
                        timestamp = datetime.now().isoformat()
                    
                    post_link = element.find_element(By.XPATH, ".//a[contains(@href, '/post/')]").get_attribute('href')
                    
                    posts.append({
                        'id': post_id,
                        'text': text,
                        'timestamp': timestamp,
                        'link': post_link,
                        'element': element
                    })
                    
                except Exception as e:
                    logger.debug(f"Пропуск елемента: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Помилка витягування постів: {e}")
        
        return posts
    
    def filter_new_posts(self, posts, account_id, keyword):
        key = f"{account_id}_{keyword}"
        last_ts = self.last_seen.get(key, 0)
        
        new_posts = []
        max_ts = last_ts
        seen_ids = set()
        
        for post in posts:
            post_id = post.get('id')
            timestamp = post.get('timestamp', '')
            
            if post_id in seen_ids:
                continue
            seen_ids.add(post_id)
            
            if not timestamp:
                new_posts.append(post)
                continue
            
            try:
                post_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                post_ts = int(post_time.timestamp())
                
                if post_ts > last_ts:
                    new_posts.append(post)
                    max_ts = max(max_ts, post_ts)
            except Exception as e:
                logger.debug(f"Помилка timestamp: {e}")
                new_posts.append(post)
        
        if max_ts > last_ts:
            self.last_seen[key] = max_ts
            self.save_json(self.data_dir / 'last_seen.json', self.last_seen)
        
        return new_posts
    
    def comment_on_post(self, post, comment_text):
        try:
            post_link = post['link']
            self.driver.get(post_link)
            time.sleep(random.uniform(3, 5))
            
            try:
                reply_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and contains(@aria-label, 'Reply')]"))
                )
                reply_button.click()
                time.sleep(random.uniform(1, 2))
            except:
                logger.warning("Не знайдено кнопку Reply, пробую альтернативний спосіб")
                try:
                    comment_area = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true']"))
                    )
                    comment_area.click()
                    time.sleep(1)
                except:
                    logger.error("Не можу знайти поле для коментаря")
                    return False
            
            comment_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
            )
            
            comment_input.click()
            time.sleep(random.uniform(0.5, 1))
            
            for char in comment_text:
                comment_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(random.uniform(1, 2))
            
            post_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and contains(text(), 'Post')]"))
            )
            post_button.click()
            
            time.sleep(random.uniform(2, 3))
            
            logger.info(f"✓ Коментар залишено: {comment_text[:30]}...")
            return True
            
        except Exception as e:
            logger.error(f"Помилка коментування: {e}")
            return False
    
    def get_comment_template(self, keyword):
        templates = self.keywords.get(keyword, {}).get('templates', [])
        if templates:
            return random.choice(templates)
        return None
    
    def log_comment(self, account_id, post_id, comment_id, keyword, status, error=None):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'account_id': account_id,
            'post_id': post_id,
            'comment_id': comment_id,
            'keyword': keyword,
            'status': status,
            'error': error
        }
        self.logs.append(log_entry)
        self.save_json(self.data_dir / 'logs.json', self.logs)
    
    def process_account(self, account_id):
        logger.info(f"=" * 50)
        logger.info(f"Обробка акаунту: {account_id}")
        logger.info(f"=" * 50)
        
        account_config = self.accounts['accounts'][account_id]
        
        if not account_config.get('enabled', True):
            logger.info(f"Акаунт {account_id} вимкнено")
            return
        
        self.init_driver(headless=account_config.get('headless', False))
        
        try:
            if not self.login(account_id):
                logger.error(f"Не вдалося увійти в акаунт {account_id}")
                return
            
            max_comments_per_run = account_config.get('max_comments_per_run', 5)
            comments_posted = 0
            
            for keyword, config in self.keywords.items():
                if not config.get('enabled', True):
                    continue
                
                if comments_posted >= max_comments_per_run:
                    logger.info(f"Досягнуто ліміт {max_comments_per_run} коментарів")
                    break
                
                posts = self.search_keyword(keyword)
                
                if not posts:
                    logger.info(f"Постів не знайдено для '{keyword}'")
                    continue
                
                new_posts = self.filter_new_posts(posts, account_id, keyword)
                logger.info(f"Знайдено {len(new_posts)} нових постів")
                
                for post in new_posts:
                    if comments_posted >= max_comments_per_run:
                        break
                    
                    post_id = post.get('id')
                    comment_text = self.get_comment_template(keyword)
                    
                    if not comment_text:
                        logger.warning(f"Немає шаблону для '{keyword}'")
                        continue
                    
                    logger.info(f"Коментування поста {post_id}")
                    
                    try:
                        success = self.comment_on_post(post, comment_text)
                        
                        if success:
                            self.log_comment(account_id, post_id, 'selenium_comment', keyword, 'success')
                            comments_posted += 1
                        else:
                            self.log_comment(account_id, post_id, None, keyword, 'failed', 'Comment failed')
                        
                        delay = random.uniform(5, 30)
                        logger.info(f"Затримка {delay:.1f}с перед наступним коментарем")
                        time.sleep(delay)
                        
                    except Exception as e:
                        logger.error(f"Помилка: {e}")
                        self.log_comment(account_id, post_id, None, keyword, 'error', str(e))
                
                time.sleep(random.uniform(5, 10))
            
        except Exception as e:
            logger.error(f"Критична помилка: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def run(self):
        logger.info("=" * 70)
        logger.info("ЗАПУСК АВТОКОМЕНТАТОРА THREADS (SELENIUM)")
        logger.info("=" * 70)
        
        for account_id in self.accounts['accounts'].keys():
            try:
                self.process_account(account_id)
            except Exception as e:
                logger.error(f"Помилка обробки акаунту {account_id}: {e}")
        
        logger.info("Цикл завершено")


def main():
    bot = ThreadsSeleniumBot()
    
    schedule.every(10).minutes.do(bot.run)
    
    logger.info("Сервіс запущено. Перший запуск...")
    bot.run()
    
    logger.info("Очікування наступного запуску (кожні 10 хвилин)")
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == '__main__':
    main()

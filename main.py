from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import random
from pathlib import Path
import schedule
import logging
from logging.handlers import TimedRotatingFileHandler
import pickle
import sys
import re
from datetime import datetime, timedelta, timezone

from database import Database

# Створюємо папку для логів
logs_dir = Path('logs')
logs_dir.mkdir(exist_ok=True)

# Налаштування логування з ротацією за добу
log_file = 'logs/bot_script.log'

# Створюємо handler з ротацією кожен день (зберігаємо 1 день)
file_handler = TimedRotatingFileHandler(
    log_file,
    when='midnight',
    interval=1,
    backupCount=1,  # Зберігаємо тільки за 1 добу
    encoding='utf-8'
)
file_handler.suffix = '%Y-%m-%d'

# Консольний handler
console_handler = logging.StreamHandler()

# Форматування
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)
console_handler.setFormatter(log_format)

# Налаштовуємо root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


class ThreadsSeleniumBot:
    def __init__(self):
        self.db = Database()
        self.sessions_dir = Path('data/sessions')
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.driver = None
    
    def has_cyrillic(self, text):
        """Перевіряє чи містить текст кирилицю (українські/російські букви)"""
        if not text:
            return False
        cyrillic_pattern = '[а-яА-ЯіїєґІЇЄҐ]'
        return bool(re.search(cyrillic_pattern, text))
    
    def get_delay(self, setting_min, setting_max):
        min_val = float(self.db.get_setting(setting_min))
        max_val = float(self.db.get_setting(setting_max))
        return random.uniform(min_val, max_val)
    
    def init_driver(self, headless=False):
        # Перевіряємо глобальне налаштування headless
        global_headless = self.db.get_setting('global_headless_mode') or 'false'
        if global_headless == 'true':
            headless = True
        
        # Використовуємо унікальну директорію для кожного запуску
        import tempfile
        import uuid
        unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
        temp_dir = tempfile.mkdtemp(prefix=f'chrome_temp_{unique_id}_')
            
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=en-US')
        # Використовуємо УНІКАЛЬНУ директорію
        options.add_argument(f'--user-data-dir={temp_dir}')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        logger.info(f"📂 Створено тимчасову директорію: {temp_dir}")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def save_session(self, account_id):
        session_file = self.sessions_dir / f"{account_id}_session.pkl"
        cookies = self.driver.get_cookies()
        with open(session_file, 'wb') as f:
            pickle.dump(cookies, f)
    
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
                logger.info(f"Сесія завантажена")
                return True
        except:
            pass
        
        return False
    
    def is_logged_in(self):
        try:
            time.sleep(2)
            try:
                self.driver.find_element(By.XPATH, "//span[contains(text(), 'New thread')]")
                return True
            except:
                pass
            
            try:
                self.driver.find_element(By.XPATH, "//input[@placeholder='Username, phone or email']")
                return False
            except:
                return True
        except:
            return False
    
    def login(self, account):
        if self.load_session(account['id']):
            return True
        
        logger.info(f"Вхід @{account['username']}")
        
        try:
            self.driver.get('https://www.threads.net/login')
            time.sleep(random.uniform(3, 5))
            
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Username, phone or email']"))
            )
            
            username_input.click()
            time.sleep(0.5)
            username_input.clear()
            
            for char in account['username']:
                username_input.send_keys(char)
                time.sleep(random.uniform(0.1, 0.2))
            
            time.sleep(0.5)
            
            password_input = self.driver.find_element(By.XPATH, "//input[@type='password']")
            password_input.click()
            time.sleep(0.5)
            
            for char in account['password']:
                password_input.send_keys(char)
                time.sleep(random.uniform(0.1, 0.2))
            
            time.sleep(0.5)
            password_input.send_keys(Keys.RETURN)
            
            logger.info("Очікування логіну...")
            time.sleep(12)
            
            for attempt in range(3):
                if self.is_logged_in():
                    logger.info("✓ Вхід успішний")
                    self.save_session(account['id'])
                    return True
                logger.info(f"Ще чекаємо... (спроба {attempt + 1}/3)")
                time.sleep(3)
            
            logger.error("Не вдалось увійти після очікування")
            return False
                
        except Exception as e:
            logger.error(f"Помилка входу: {e}")
            return False
    
    def search_keyword(self, keyword, max_posts_needed):
        try:
            logger.info(f"Пошук: {keyword} (потрібно {max_posts_needed} постів)")
            
            # ФІЛЬТР RECENT - шукаємо свіжі пости
            search_url = f"https://www.threads.net/search?q={keyword}&filter=recent"
            self.driver.get(search_url)
            
            logger.info("Очікування завантаження (8 сек)...")
            time.sleep(8)
            
            found_posts = []
            scroll_attempts = 0
            max_scrolls = 20
            
            while len(found_posts) < max_posts_needed and scroll_attempts < max_scrolls:
                scroll_attempts += 1
                
                # Скролимо
                self.driver.execute_script("window.scrollBy(0, 600);")
                time.sleep(2)
                
                # Витягуємо пости
                current_posts = self.extract_posts_from_page()
                
                # Додаємо нові унікальні пости
                for post in current_posts:
                    if post['id'] not in [p['id'] for p in found_posts]:
                        found_posts.append(post)
                
                logger.info(f"Скрол {scroll_attempts}: знайдено {len(found_posts)}/{max_posts_needed} постів")
                
                if len(found_posts) >= max_posts_needed:
                    break
            
            # Фільтруємо за віком
            max_age_hours = int(self.db.get_setting('max_post_age_hours'))
            if max_age_hours > 0:
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
                filtered = [p for p in found_posts if p['timestamp'] >= cutoff_time]
                
                if len(filtered) < len(found_posts):
                    logger.info(f"Відфільтровано {len(found_posts) - len(filtered)} старих постів (>{max_age_hours}h)")
                
                found_posts = filtered
            
            logger.info(f"✅ Знайдено {len(found_posts)} постів з кирилицею")
            
            # Виводимо топ-5
            if found_posts:
                logger.info("Топ-5 постів:")
                for i, post in enumerate(found_posts[:5], 1):
                    logger.info(f"  #{i}: [{post['time_text']}] {post['text_preview'][:60]}...")
            
            return found_posts[:max_posts_needed]
            
        except Exception as e:
            logger.error(f"❌ Помилка пошуку: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def extract_posts_from_page(self):
        """Витягує пости з поточної сторінки"""
        posts = []
        seen_ids = set()
        
        try:
            # Знаходимо всі посилання на пости
            all_post_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/post/')]")
            
            logger.info(f"  Знайдено {len(all_post_links)} посилань на сторінці")
            
            for link in all_post_links:
                try:
                    href = link.get_attribute('href')
                    if not href or '/media' in href:
                        continue
                    
                    post_id = href.split('/')[-1].split('?')[0]
                    
                    if post_id in seen_ids:
                        continue
                    seen_ids.add(post_id)
                    
                    # Шукаємо батьківський контейнер
                    parent = link
                    for _ in range(8):
                        try:
                            parent = parent.find_element(By.XPATH, "..")
                        except:
                            break
                    
                    # Витягуємо весь текст з контейнера
                    full_text = parent.text
                    
                    # Розбиваємо на рядки
                    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                    
                    # Шукаємо основний текст поста (довгі рядки з кирилицею)
                    post_text_lines = []
                    for line in lines:
                        # Пропускаємо короткі рядки, username, кнопки
                        if len(line) < 15:
                            continue
                        if any(x in line.lower() for x in ['reply', 'like', 'repost', 'view', 'translate', 'follow']):
                            continue
                        # Якщо рядок містить кирилицю - додаємо
                        if self.has_cyrillic(line):
                            post_text_lines.append(line)
                    
                    # Якщо немає кирилиці - пропускаємо
                    if not post_text_lines:
                        continue
                    
                    post_text = ' '.join(post_text_lines)
                    
                    logger.info(f"  ✅ Пост {post_id}: {post_text[:60]}...")
                    
                    # Шукаємо час
                    post_time = datetime.now(timezone.utc)
                    time_text = "now"
                    
                    try:
                        time_elem = parent.find_element(By.TAG_NAME, "time")
                        datetime_attr = time_elem.get_attribute('datetime')
                        if datetime_attr:
                            post_time = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        time_text = time_elem.text or time_text
                    except:
                        # Шукаємо текст типу "1h", "2d"
                        for line in lines:
                            if len(line) < 5 and any(c in line for c in ['h', 'm', 'd', 's', 'w']):
                                time_text = line
                                post_time = self.parse_time_ago(line)
                                break
                    
                    posts.append({
                        'id': post_id,
                        'link': href,
                        'timestamp': post_time,
                        'time_text': time_text,
                        'text_preview': post_text[:150]
                    })
                    
                except Exception as e:
                    continue
            
            logger.info(f"  Витягнуто {len(posts)} постів з кирилицею")
            return posts
            
        except Exception as e:
            logger.error(f"  ❌ Помилка: {e}")
            return posts
    
    def parse_time_ago(self, time_text):
        """Конвертує текст типу '2h', '5m', '1d' в timestamp"""
        try:
            time_text = time_text.lower().strip()
            now = datetime.now(timezone.utc)
            
            if 's' in time_text or 'sec' in time_text:
                seconds = int(''.join(filter(str.isdigit, time_text)))
                post_time = now - timedelta(seconds=seconds)
            elif 'm' in time_text or 'min' in time_text:
                minutes = int(''.join(filter(str.isdigit, time_text)))
                post_time = now - timedelta(minutes=minutes)
            elif 'h' in time_text or 'hour' in time_text:
                hours = int(''.join(filter(str.isdigit, time_text)))
                post_time = now - timedelta(hours=hours)
            elif 'd' in time_text or 'day' in time_text:
                days = int(''.join(filter(str.isdigit, time_text)))
                post_time = now - timedelta(days=days)
            elif 'w' in time_text or 'week' in time_text:
                weeks = int(''.join(filter(str.isdigit, time_text)))
                post_time = now - timedelta(weeks=weeks)
            else:
                post_time = now - timedelta(days=365)
            
            return post_time
        except:
            return datetime.now(timezone.utc) - timedelta(days=365)
    
    def follow_user(self):
        """Підписатися на автора поста - переходимо на профіль"""
        try:
            logger.info("Підписуємося на автора через профіль...")
            
            # СКРОЛИМО ВГОРУ до початку поста
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(3)
            
            # Знаходимо посилання на профіль автора ПОСТА (не коментарів)
            try:
                profile_url = None
                username = None
                
                # Витягуємо username з URL поста
                # URL виглядає як: https://www.threads.net/@USERNAME/post/POST_ID
                current_url = self.driver.current_url
                logger.info(f"Поточний URL: {current_url}")
                
                match = re.search(r'/@([^/]+)/', current_url)
                if match:
                    username = match.group(1)
                    profile_url = f"https://www.threads.com/@{username}"
                    logger.info(f"Знайдено автора: {username}")
                else:
                    logger.error("❌ Не вдалося витягнути username з URL")
                    return False
                
                if not profile_url:
                    logger.error("❌ Не знайдено посилання на профіль автора")
                    return False
                
                logger.info(f"Переходимо на профіль: {profile_url}")
                
                # ПЕРЕХОДИМО НА ПРОФІЛЬ АВТОРА
                self.driver.get(profile_url)
                time.sleep(4)
                
                # Шукаємо кнопку Follow на сторінці профілю
                logger.info("Шукаємо кнопку Follow на профілі...")
                
                follow_found = False
                
                # Спочатку шукаємо всі кнопки та div з роллю button
                try:
                    all_buttons = self.driver.find_elements(By.XPATH, "//button | //div[@role='button']")
                    
                    for btn in all_buttons:
                        try:
                            if not btn.is_displayed():
                                continue
                            
                            btn_text = btn.text.strip()
                            
                            # Шукаємо Follow (не Following, не Followers)
                            if btn_text == 'Follow' or (btn_text and 'Follow' in btn_text and 'Following' not in btn_text and 'Followers' not in btn_text):
                                logger.info(f"✅ Знайдено кнопку Follow")
                                
                                # Скролимо до кнопки
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                time.sleep(1)
                                
                                try:
                                    btn.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", btn)
                                
                                time.sleep(2)
                                logger.info("✅ Підписка виконана")
                                follow_found = True
                                break
                        except Exception as e:
                            continue
                except Exception as e:
                    logger.error(f"Помилка пошуку кнопок: {e}")
                
                if not follow_found:
                    logger.warning("⚠️ Кнопка Follow не знайдена на профілі (можливо вже підписані)")
                
                # ПОВЕРТАЄМОСЯ НАЗАД НА ПОСТ
                logger.info("Повертаємося назад на пост...")
                self.driver.back()
                time.sleep(4)
                
                return follow_found
                
            except Exception as e:
                logger.error(f"❌ Помилка при переході на профіль: {e}")
                # Спробуємо повернутися назад
                try:
                    self.driver.back()
                    time.sleep(3)
                except:
                    pass
                return False
            
        except Exception as e:
            logger.error(f"❌ Помилка підписки: {e}")
            return False
    
    def comment_on_post(self, post, comment_text, should_follow=False):
        try:
            logger.info(f"Коментуємо пост ({post['time_text']})")
            self.driver.get(post['link'])
            time.sleep(5)
            
            # Підписка ПЕРЕД коментуванням (якщо потрібно)
            if should_follow:
                self.follow_user()
                # Вже на сторінці поста після driver.back()
                logger.info("Продовжуємо коментування...")
                time.sleep(2)
            
            reply_texts = ["Reply to", "Reply", "Відповісти"]
            clicked = False
            
            for reply_text in reply_texts:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{reply_text}')]")
                    
                    for elem in elements:
                        try:
                            if elem.is_displayed():
                                try:
                                    elem.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", elem)
                                
                                clicked = True
                                time.sleep(2)
                                break
                        except:
                            continue
                    
                    if clicked:
                        break
                except:
                    continue
            
            time.sleep(2)
            
            comment_field = None
            field_selectors = [
                "//div[@contenteditable='true']",
                "//textarea[@placeholder]",
                "//div[@role='textbox']",
            ]
            
            for selector in field_selectors:
                try:
                    fields = self.driver.find_elements(By.XPATH, selector)
                    
                    for field in fields:
                        try:
                            if field.is_displayed() and field.is_enabled():
                                comment_field = field
                                break
                        except:
                            continue
                    
                    if comment_field:
                        break
                except:
                    pass
            
            if not comment_field:
                logger.error("❌ Поле для коментаря не знайдено")
                return False
            
            try:
                comment_field.click()
            except:
                self.driver.execute_script("arguments[0].click();", comment_field)
            
            time.sleep(1)
            
            try:
                comment_field.clear()
            except:
                pass
            
            time.sleep(0.5)
            
            for char in comment_text:
                comment_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(2)
            
            post_button = None
            post_selectors = [
                "//div[@role='button' and text()='Post']",
                "//button[text()='Post']",
                "//*[text()='Post']",
            ]
            
            for selector in post_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    
                    for btn in buttons:
                        try:
                            if btn.is_displayed() and btn.is_enabled():
                                post_button = btn
                                break
                        except:
                            continue
                    
                    if post_button:
                        break
                except:
                    continue
            
            if post_button:
                try:
                    post_button.click()
                except:
                    self.driver.execute_script("arguments[0].click();", post_button)
                
                time.sleep(3)
                logger.info("✅ Коментар опубліковано")
                return True
            else:
                comment_field.send_keys(Keys.RETURN)
                time.sleep(3)
                logger.info("✅ Enter надіслано")
                return True
            
        except Exception as e:
            logger.error(f"❌ Помилка коментування: {e}")
            return False
    
    def process_account(self, account):
        logger.info(f"=" * 50)
        logger.info(f"Акаунт: @{account['username']}")
        logger.info(f"=" * 50)
        
        self.init_driver()
        
        try:
            if not self.login(account):
                logger.error("❌ Вхід не вдався")
                return
            
            comments_posted = 0
            max_comments = account['max_comments_per_run']
            
            keywords = [k for k in self.db.get_all_keywords() if k['enabled']]
            
            for keyword_data in keywords:
                if comments_posted >= max_comments:
                    logger.info(f"Ліміт {max_comments} досягнуто")
                    break
                
                keyword = keyword_data['keyword']
                should_follow = keyword_data.get('should_follow', False)
                remaining_comments = max_comments - comments_posted
                
                # Шукаємо стільки постів, скільки ще потрібно прокоментувати
                posts = self.search_keyword(keyword, remaining_comments)
                
                if not posts:
                    logger.warning(f"⚠️ Постів не знайдено для '{keyword}'")
                    continue
                
                templates = self.db.get_templates_for_keyword(keyword_data['id'])
                if not templates:
                    logger.warning(f"⚠️ Немає шаблонів для {keyword}")
                    continue
                
                for post in posts:
                    if comments_posted >= max_comments:
                        break
                    
                    if self.db.is_post_commented(account['id'], post['id']):
                        logger.info(f"ℹ️ Пост {post['id']} вже коментували, пропускаємо")
                        continue
                    
                    comment_text = random.choice(templates)['template_text']
                    
                    # Передаємо should_follow в функцію коментування
                    success = self.comment_on_post(post, comment_text, should_follow)
                    
                    status = 'success' if success else 'failed'
                    self.db.add_comment_history(
                        account['id'],
                        post['id'],
                        post['link'],
                        keyword,
                        comment_text,
                        status
                    )
                    
                    if success:
                        comments_posted += 1
                        if should_follow:
                            logger.info(f"📊 Коментарів: {comments_posted}/{max_comments} (+ підписка)")
                        else:
                            logger.info(f"📊 Коментарів: {comments_posted}/{max_comments}")
                    
                    delay = self.get_delay('delay_between_comments_min', 'delay_between_comments_max')
                    logger.info(f"⏳ Затримка {delay:.1f}с")
                    time.sleep(delay)
                
                delay = self.get_delay('delay_between_posts_min', 'delay_between_posts_max')
                time.sleep(delay)
            
            logger.info(f"✅ Завершено! Коментарів: {comments_posted}")
            
        except Exception as e:
            logger.error(f"❌ Помилка: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def run(self):
        logger.info("=" * 70)
        logger.info("🚀 ЗАПУСК БОТА")
        logger.info("=" * 70)
        
        accounts = [a for a in self.db.get_all_accounts() if a['enabled']]
        
        if not accounts:
            logger.error("❌ Немає активних акаунтів")
            return
        
        for account in accounts:
            try:
                self.process_account(account)
                
                if account != accounts[-1]:
                    delay = self.get_delay('delay_between_accounts_min', 'delay_between_accounts_max')
                    logger.info(f"⏳ Затримка між акаунтами: {delay:.1f}с")
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"❌ Помилка: {e}")
        
        logger.info("✅ Цикл завершено")


def main():
    bot = ThreadsSeleniumBot()
    
    if '--once' in sys.argv:
        logger.info("ℹ️ Режим: один запуск")
        bot.run()
    else:
        db = Database()
        interval = int(db.get_setting('run_interval_minutes'))
        
        schedule.every(interval).minutes.do(bot.run)
        
        logger.info(f"🔄 Перший запуск...")
        bot.run()
        
        logger.info(f"⏰ Очікування (кожні {interval} хвилин)")
        while True:
            schedule.run_pending()
            time.sleep(30)


if __name__ == '__main__':
    main()

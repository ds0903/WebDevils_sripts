from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import logging
import time
import random

logger = logging.getLogger(__name__)


def create_driver(headless=False, user_agent=None):
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
    
    if user_agent:
        options.add_argument(f'user-agent={user_agent}')
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def random_delay(min_sec=1, max_sec=3):
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay


def human_type(element, text, min_delay=0.05, max_delay=0.15):
    element.click()
    time.sleep(random.uniform(0.2, 0.5))
    
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))
    
    time.sleep(random.uniform(0.3, 0.7))


def scroll_page(driver, scrolls=3, delay_range=(2, 4)):
    for i in range(scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(*delay_range))


def wait_and_click(driver, by, value, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        return True
    except Exception as e:
        logger.error(f"Не вдалося знайти/клікнути елемент: {e}")
        return False


def safe_find_element(driver, by, value, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except Exception as e:
        logger.debug(f"Елемент не знайдено: {e}")
        return None


def check_rate_limit(driver):
    try:
        error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Try again later')]")
        if error_elements:
            logger.warning("Виявлено rate limit!")
            return True
    except:
        pass
    return False

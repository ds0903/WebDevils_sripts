from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import time
from pathlib import Path

def test_login():
    print("🔍 Тест входу в Threads")
    print("="*60)
    
    config_file = Path('config/accounts.json')
    if not config_file.exists():
        print("❌ Файл config/accounts.json не знайдено!")
        return
    
    with open(config_file, 'r', encoding='utf-8') as f:
        accounts = json.load(f)
    
    if not accounts['accounts']:
        print("❌ Немає налаштованих акаунтів!")
        return
    
    account_id = list(accounts['accounts'].keys())[0]
    account = accounts['accounts'][account_id]
    
    username = account.get('username')
    password = account.get('password')
    
    if not username or not password:
        print("❌ Немає username або password в конфігурації!")
        print("Відредагуйте config/accounts.json")
        return
    
    print(f"\n📝 Тестуємо акаунт: {account_id}")
    print(f"👤 Username: {username}")
    print(f"\n⏳ Запускаємо браузер...\n")
    
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        print("🌐 Відкриваємо Threads...")
        driver.get('https://www.threads.net/login')
        time.sleep(3)
        
        print("⌨️  Вводимо дані...")
        username_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='username']"))
        )
        username_input.send_keys(username)
        time.sleep(1)
        
        password_input = driver.find_element(By.XPATH, "//input[@name='password']")
        password_input.send_keys(password)
        time.sleep(1)
        
        print("🔐 Виконуємо вхід...")
        password_input.send_keys(Keys.RETURN)
        
        time.sleep(5)
        
        try:
            driver.find_element(By.XPATH, "//input[@placeholder='Search']")
            print("\n✅ УСПІХ! Вхід виконано!")
            print("🎉 Акаунт працює правильно!\n")
        except:
            print("\n⚠️  Можливо виникла проблема з входом")
            print("Перевірте браузер вручну\n")
        
        input("Натисніть Enter щоб закрити браузер...")
        
    except Exception as e:
        print(f"\n❌ Помилка: {e}")
    
    finally:
        driver.quit()
        print("\n✅ Браузер закрито")


if __name__ == '__main__':
    test_login()

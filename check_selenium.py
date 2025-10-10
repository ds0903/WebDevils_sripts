from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

print("🔍 Перевірка Selenium та ChromeDriver\n")

try:
    print("1. Ініціалізація драйвера...")
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    print("   ✅ Драйвер створено успішно!\n")
    
    print("2. Відкриваємо Google...")
    driver.get('https://www.google.com')
    time.sleep(2)
    print("   ✅ Сторінка відкрилася!\n")
    
    print("3. Відкриваємо Threads...")
    driver.get('https://www.threads.net')
    time.sleep(3)
    print("   ✅ Threads завантажено!\n")
    
    print("✅ ВСЕ ПРАЦЮЄ! Selenium налаштовано правильно.\n")
    
    input("Натисни Enter щоб закрити браузер...")
    driver.quit()
    
except Exception as e:
    print(f"\n❌ ПОМИЛКА: {e}\n")
    print("Деталі:")
    import traceback
    traceback.print_exc()

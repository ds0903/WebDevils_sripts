from main import ThreadsSeleniumBot
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("🤖 Threads Auto Commenter - Разовий запуск")
print("="*60)
print("\nЗапускаємо бота один раз (без циклу)...\n")

bot = ThreadsSeleniumBot()
bot.run()

print("\n✅ Робота завершена!")
print("Для постійної роботи використовуйте: python main.py")

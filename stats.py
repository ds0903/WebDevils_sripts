import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

def load_logs():
    logs_file = Path('data/logs.json')
    if not logs_file.exists():
        return []
    
    with open(logs_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def overall_stats(logs):
    print("\n" + "="*60)
    print("📊 ЗАГАЛЬНА СТАТИСТИКА")
    print("="*60)
    
    if not logs:
        print("\n⚠️ Логів не знайдено")
        return
    
    total = len(logs)
    success = len([l for l in logs if l['status'] == 'success'])
    failed = len([l for l in logs if l['status'] in ['failed', 'error']])
    
    print(f"\n📝 Всього спроб: {total}")
    print(f"✅ Успішних: {success} ({success/total*100:.1f}%)")
    print(f"❌ Невдалих: {failed} ({failed/total*100:.1f}%)")
    
    if logs:
        first = datetime.fromisoformat(logs[0]['timestamp'])
        last = datetime.fromisoformat(logs[-1]['timestamp'])
        print(f"\n📅 Перший запис: {first.strftime('%Y-%m-%d %H:%M')}")
        print(f"📅 Останній запис: {last.strftime('%Y-%m-%d %H:%M')}")


def keyword_stats(logs):
    print("\n" + "="*60)
    print("🔑 СТАТИСТИКА ПО КЛЮЧОВИМ СЛОВАМ")
    print("="*60)
    
    keyword_data = defaultdict(lambda: {'total': 0, 'success': 0})
    
    for log in logs:
        kw = log.get('keyword', 'unknown')
        keyword_data[kw]['total'] += 1
        if log['status'] == 'success':
            keyword_data[kw]['success'] += 1
    
    sorted_keywords = sorted(
        keyword_data.items(),
        key=lambda x: x[1]['total'],
        reverse=True
    )
    
    for keyword, data in sorted_keywords:
        success_rate = data['success'] / data['total'] * 100 if data['total'] > 0 else 0
        print(f"\n📌 {keyword}")
        print(f"   Всього: {data['total']}")
        print(f"   Успішно: {data['success']} ({success_rate:.1f}%)")


def main():
    logs = load_logs()
    overall_stats(logs)
    keyword_stats(logs)


if __name__ == '__main__':
    main()

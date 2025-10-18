from aiogram import Router, F
from aiogram.types import CallbackQuery
import subprocess
import os
import psutil

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import Database
from bot.utils import is_authorized, logger
from bot.keyboards_aiogram import run_menu_markup, back_button_markup
from bot.config import BASE_DIR

router = Router()
db = Database()

@router.callback_query(F.data == "menu_run")
async def show_run_menu(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    accounts = [a for a in db.get_all_accounts() if a['enabled']]
    keywords = [k for k in db.get_all_keywords() if k['enabled']]
    
    text = "═══════════════════════════════════\n"
    text += "  🚀 <b>ЗАПУСК БОТА</b>\n"
    text += "═══════════════════════════════════\n\n"
    
    if not accounts:
        text += "❌ Немає активних акаунтів!\n\n"
    else:
        text += f"✅ Активних акаунтів: {len(accounts)}\n"
    
    if not keywords:
        text += "❌ Немає активних ключових слів!\n\n"
    else:
        text += f"✅ Активних ключових слів: {len(keywords)}\n"
        
        follow_keywords = [k for k in keywords if k.get('should_follow', False)]
        if follow_keywords:
            kw_list = ', '.join([f'"{k["keyword"]}"' for k in follow_keywords[:3]])
            if len(follow_keywords) > 3:
                kw_list += f" та ще {len(follow_keywords) - 3}"
            text += f"👤 З підпискою: {len(follow_keywords)}\n   ({kw_list})\n"
    
    if not accounts or not keywords:
        await callback.message.edit_text(text, reply_markup=back_button_markup(), parse_mode='HTML')
        logger.warning("Спроба запуску без акаунтів/ключових слів")
        await callback.answer()
        return
    
    text += "\n<b>Виберіть режим роботи:</b>"
    
    await callback.message.edit_text(text, reply_markup=run_menu_markup(), parse_mode='HTML')
    await callback.answer()

@router.callback_query(F.data == "run_once")
async def run_bot_once(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    # Видаляємо попереднє повідомлення
    try:
        await callback.message.delete()
    except:
        pass
    
    try:
        # Запускаємо Python скрипт напряму
        subprocess.Popen(
            [sys.executable, 'main.py', '--once'],
            cwd=BASE_DIR
        )
        
        await callback.message.answer(
            f"✅ <b>Бот запущено один раз!</b>\n\n"
            f"⚠️ Для зупинки використовуйте кнопку <b>🛑 Зупинити бота</b>",
            parse_mode='HTML',
            reply_markup=back_button_markup()
        )
        logger.info("✅ Бот запущено в режимі 'один раз'")
    except Exception as e:
        logger.error(f"Помилка запуску бота: {e}")
        await callback.message.answer(
            f"❌ <b>Помилка запуску:</b> {e}",
            parse_mode='HTML',
            reply_markup=back_button_markup()
        )
    
    await callback.answer()

@router.callback_query(F.data == "run_loop")
async def run_bot_loop(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    # Видаляємо попереднє повідомлення
    try:
        await callback.message.delete()
    except:
        pass
    
    try:
        # Запускаємо Python скрипт напряму
        subprocess.Popen(
            [sys.executable, 'main.py'],
            cwd=BASE_DIR
        )
        
        await callback.message.answer(
            f"✅ <b>Бот запущено в циклі!</b>\n\n"
            f"⚠️ Для зупинки використовуйте кнопку <b>🛑 Зупинити бота</b>",
            parse_mode='HTML',
            reply_markup=back_button_markup()
        )
        logger.info("✅ Бот запущено в циклічному режимі")
    except Exception as e:
        logger.error(f"Помилка запуску бота в циклі: {e}")
        await callback.message.answer(
            f"❌ <b>Помилка запуску:</b> {e}",
            parse_mode='HTML',
            reply_markup=back_button_markup()
        )
    
    await callback.answer()

@router.callback_query(F.data == "run_stop")
async def stop_bot(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    await callback.answer("🔍 Шукаю процеси...")
    
    # Видаляємо попереднє повідомлення
    try:
        await callback.message.delete()
    except:
        pass
    
    try:
        killed_count = 0
        found_processes = []
        
        # Отримуємо абсолютний шлях до папки проекту
        project_dir = os.path.abspath(BASE_DIR)
        logger.info(f"Шукаємо процеси python main.py в директорії: {project_dir}")
        
        # Шукаємо всі процеси python що запускають main.py
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
            try:
                # Перевіряємо чи це python процес
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and any('main.py' in str(arg) for arg in cmdline):
                        # Знайшли процес main.py - перевіряємо робочу директорію
                        try:
                            proc_cwd = proc.cwd()
                            logger.info(f"Знайдено процес python main.py PID {proc.info['pid']}, cwd: {proc_cwd}")
                            
                            # КРИТИЧНО: Перевіряємо чи процес з НАШОЇ папки
                            if proc_cwd == project_dir or proc_cwd.startswith(project_dir):
                                found_processes.append(proc.info['pid'])
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            # Якщо не можемо отримати cwd - краще пропустити
                            logger.warning(f"Не можу перевірити cwd для процесу {proc.info['pid']}, пропускаємо")
                            continue
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                continue
        
        # Зупиняємо знайдені процеси
        for pid in found_processes:
            try:
                proc = psutil.Process(pid)
                logger.info(f"Зупиняємо процес PID: {pid}")
                proc.terminate()  # М'яка зупинка
                try:
                    proc.wait(timeout=3)  # Чекаємо 3 секунди
                except psutil.TimeoutExpired:
                    logger.warning(f"Процес {pid} не завершився, примусова зупинка")
                    proc.kill()  # Примусова зупинка
                killed_count += 1
                logger.info(f"✅ Зупинено процес PID: {pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.error(f"Помилка зупинки процесу {pid}: {e}")
                continue
        
        if killed_count > 0:
            await callback.message.answer(
                f"✅ <b>Бот зупинено!</b>\n\n"
                f"Завершено процесів: {killed_count}\n"
                f"📁 Директорія: {project_dir}",
                parse_mode='HTML',
                reply_markup=back_button_markup()
            )
            logger.info(f"✅ Бот зупинено (завершено {killed_count} процесів)")
        else:
            await callback.message.answer(
                "⚠️ <b>Бот не запущений</b>\n\n"
                f"Процеси python main.py не знайдено в директорії:\n<code>{project_dir}</code>",
                parse_mode='HTML',
                reply_markup=back_button_markup()
            )
            logger.info("⚠️ Процеси python main.py не знайдено")
        
    except Exception as e:
        logger.error(f"Помилка зупинки бота: {e}")
        import traceback
        traceback.print_exc()
        await callback.message.answer(
            f"❌ <b>Помилка зупинки:</b> {e}",
            parse_mode='HTML',
            reply_markup=back_button_markup()
        )

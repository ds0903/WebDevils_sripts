@echo off
chcp 65001 > nul
title Встановлення залежностей

echo ========================================
echo 📦 Встановлення залежностей
echo ========================================
echo.

echo Оновлення pip...
python -m pip install --upgrade pip
echo.

echo Встановлення пакетів з requirements.txt...
pip install -r requirements.txt
echo.

echo ========================================
echo ✅ Встановлення завершено!
echo ========================================
echo.
echo Тепер можна запустити бота:
echo   start.bat
echo.

pause

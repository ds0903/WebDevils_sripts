@echo off
chcp 65001 > nul
title Threads Auto Commenter

cd /d "%~dp0"

python launcher.py

pause

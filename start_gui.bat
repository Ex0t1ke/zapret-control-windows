@echo off
chcp 65001 > nul
cd /d "%~dp0"

:: Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Запрос прав Администратора для работы с WinDivert...
    powershell -NoProfile -Command "Start-Process 'cmd.exe' -ArgumentList '/c \"\"%~f0\" admin\"' -Verb RunAs"
    exit /b
)

title Zapret Desktop Control
echo [INFO] Запуск графического интерфейса Zapret Desktop Control...
python run_app.py

@echo off
if not exist venv (
    echo Виртуальное окружение не найдено! Запустите setup.bat сначала.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python hysteria_checker.py
pause


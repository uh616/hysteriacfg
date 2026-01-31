@echo off
echo ========================================
echo Hysteria2 Checker - Setup Script
echo ========================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python не найден! Установите Python 3.8 или выше.
    pause
    exit /b 1
)

echo [1/3] Создание виртуального окружения...
if exist venv (
    echo Виртуальное окружение уже существует. Пропускаем...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Не удалось создать виртуальное окружение!
        pause
        exit /b 1
    )
    echo [OK] Виртуальное окружение создано.
)

echo.
echo [2/3] Активация виртуального окружения...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Не удалось активировать виртуальное окружение!
    pause
    exit /b 1
)

echo.
echo [3/3] Установка зависимостей...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Не удалось установить зависимости!
    pause
    exit /b 1
)

echo.
echo ========================================
echo [OK] Установка завершена успешно!
echo ========================================
echo.
echo Для запуска скрипта используйте:
echo   python hysteria_checker.py
echo.
pause


#!/bin/bash

echo "========================================"
echo "Hysteria2 Checker - Setup Script"
echo "========================================"
echo ""

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 не найден! Установите Python 3.8 или выше."
    exit 1
fi

echo "[1/3] Создание виртуального окружения..."
if [ -d "venv" ]; then
    echo "Виртуальное окружение уже существует. Пропускаем..."
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Не удалось создать виртуальное окружение!"
        exit 1
    fi
    echo "[OK] Виртуальное окружение создано."
fi

echo ""
echo "[2/3] Активация виртуального окружения..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[ERROR] Не удалось активировать виртуальное окружение!"
    exit 1
fi

echo ""
echo "[3/3] Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Не удалось установить зависимости!"
    exit 1
fi

echo ""
echo "========================================"
echo "[OK] Установка завершена успешно!"
echo "========================================"
echo ""
echo "Для запуска скрипта используйте:"
echo "  python hysteria_checker.py"
echo ""


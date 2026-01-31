#!/bin/bash

if [ ! -d "venv" ]; then
    echo "Виртуальное окружение не найдено! Запустите setup.sh сначала."
    exit 1
fi

source venv/bin/activate
python hysteria_checker.py


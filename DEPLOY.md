# 🚀 Инструкция по развертыванию на GitHub

## Шаг 1: Создайте репозиторий на GitHub

1. Перейдите на https://github.com/new
2. Создайте новый репозиторий (например: `hysteria2-configs`)
3. **НЕ** инициализируйте с README, .gitignore или лицензией
4. Скопируйте URL репозитория (например: `https://github.com/your-username/hysteria2-configs.git`)

## Шаг 2: Подключите локальный репозиторий к GitHub

Выполните в терминале (в директории проекта):

```bash
git remote add origin https://github.com/your-username/hysteria2-configs.git
git push -u origin main
```

## Шаг 3: Настройте GitHub Actions

GitHub Actions уже настроен в файле `.github/workflows/update_configs.yml`

Он будет автоматически:
- Запускаться каждый час
- Проверять конфиги
- Обновлять `subscription.txt` и `README.md`
- Коммитить изменения

## Шаг 4: Используйте ссылку подписки

После первого запуска GitHub Actions используйте:

```
https://raw.githubusercontent.com/your-username/hysteria2-configs/main/subscription.txt
```

## Альтернатива: Использование GitHub CLI

Если у вас установлен GitHub CLI:

```bash
gh repo create hysteria2-configs --public --source=. --remote=origin --push
```

Это автоматически создаст репозиторий и загрузит код.


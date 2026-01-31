# Настройка GitHub репозитория для автоматического обновления

## Шаг 1: Создание GitHub репозитория

1. Создайте новый репозиторий на GitHub (например: `your-username/hysteria2-configs`)
2. Склонируйте репозиторий локально или используйте веб-интерфейс

## Шаг 2: Настройка GitHub Token

1. Перейдите в Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Создайте новый токен с правами:
   - `repo` (полный доступ к репозиториям)
3. Скопируйте токен

## Шаг 3: Настройка Secrets для GitHub Actions

1. В вашем репозитории перейдите в Settings → Secrets and variables → Actions
2. Добавьте секрет:
   - Name: `GITHUB_TOKEN`
   - Value: ваш токен из шага 2

## Шаг 4: Локальная настройка (опционально)

Если хотите запускать скрипт локально с загрузкой в GitHub:

**Windows:**
```cmd
set GITHUB_TOKEN=your_token_here
set GITHUB_REPO_NAME=your-username/repo-name
set GITHUB_BRANCH=main
python hysteria_checker.py
```

**Linux/Mac:**
```bash
export GITHUB_TOKEN=your_token_here
export GITHUB_REPO_NAME=your-username/repo-name
export GITHUB_BRANCH=main
python hysteria_checker.py
```

## Шаг 5: Использование подписки

После настройки, ваша ссылка на подписку будет:

```
https://raw.githubusercontent.com/your-username/repo-name/main/subscription.txt
```

Используйте эту ссылку в вашем Hysteria2 клиенте для автоматического обновления конфигов.

## Автоматическое обновление

GitHub Actions будет автоматически запускать скрипт каждый час и обновлять файл `subscription.txt` с рабочими конфигами.

Вы также можете запустить обновление вручную:
1. Перейдите в Actions в вашем репозитории
2. Выберите workflow "Update Hysteria2 Configs"
3. Нажмите "Run workflow"

## Структура репозитория

После первого запуска в репозитории будут созданы:

- `subscription.txt` - файл с рабочими конфигами (для подписки)
- `README.md` - автоматически генерируемый README со статистикой
- `results/` - папка с детальными результатами проверки (локально)


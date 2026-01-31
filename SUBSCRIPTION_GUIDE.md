# 📝 Руководство по использованию подписки

## Что было добавлено

✅ **70+ новых источников конфигов** - добавлены актуальные GitHub репозитории с Hysteria2 конфигами

✅ **Автоматическая загрузка в GitHub** - скрипт может автоматически загружать результаты в ваш репозиторий

✅ **Файл подписки** - создается `subscription.txt` с рабочими конфигами

✅ **GitHub Actions** - автоматическое обновление каждый час

## Быстрый старт

### 1. Создайте GitHub репозиторий

```bash
# На GitHub создайте новый репозиторий, например: hysteria2-configs
```

### 2. Настройте переменные окружения

**Windows (PowerShell):**
```powershell
$env:GITHUB_TOKEN="your_github_token"
$env:GITHUB_REPO_NAME="your-username/hysteria2-configs"
$env:GITHUB_BRANCH="main"
```

**Windows (CMD):**
```cmd
set GITHUB_TOKEN=your_github_token
set GITHUB_REPO_NAME=your-username/hysteria2-configs
set GITHUB_BRANCH=main
```

**Linux/Mac:**
```bash
export GITHUB_TOKEN=your_github_token
export GITHUB_REPO_NAME=your-username/hysteria2-configs
export GITHUB_BRANCH=main
```

### 3. Запустите скрипт

```bash
python hysteria_checker.py
```

Скрипт автоматически:
- Проверит все конфиги
- Создаст `subscription.txt` с рабочими конфигами
- Загрузит файл в GitHub
- Создаст README.md со статистикой

### 4. Используйте ссылку подписки

После первого запуска используйте эту ссылку в вашем Hysteria2 клиенте:

```
https://raw.githubusercontent.com/your-username/hysteria2-configs/main/subscription.txt
```

## Автоматическое обновление через GitHub Actions

1. Загрузите файл `.github/workflows/update_configs.yml` в ваш репозиторий
2. В Settings → Secrets добавьте `GITHUB_TOKEN` (если используете свой токен)
3. GitHub Actions будет автоматически запускать скрипт каждый час

## Что создается в репозитории

- **subscription.txt** - файл с рабочими конфигами (для подписки)
- **README.md** - автоматически генерируемый README со статистикой
- **results/** - папка с детальными результатами (только локально)

## Получение GitHub Token

1. Перейдите: https://github.com/settings/tokens
2. Нажмите "Generate new token (classic)"
3. Выберите права: `repo` (полный доступ)
4. Скопируйте токен

## Пример использования в клиенте

### Hysteria2 (официальный клиент)
1. Откройте настройки
2. Добавьте подписку: `https://raw.githubusercontent.com/your-username/repo/main/subscription.txt`
3. Конфиги будут автоматически обновляться

### Clash
Добавьте в конфиг:
```yaml
proxy-providers:
  hysteria2:
    type: http
    url: https://raw.githubusercontent.com/your-username/repo/main/subscription.txt
    interval: 3600
```

## Проверка работы

После запуска скрипта вы увидите:
```
📝 Создан файл подписки: subscription.txt (X конфигов)
📤 Загрузка файлов в GitHub...
✅ Обновлен файл subscription.txt в GitHub
✅ Создан файл README.md в GitHub
🔗 URL подписки: https://raw.githubusercontent.com/...
```


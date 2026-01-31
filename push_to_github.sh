#!/bin/bash
# Скрипт для загрузки в GitHub
# Использование: ./push_to_github.sh your-username/hysteria2-configs

if [ -z "$1" ]; then
    echo "❌ Укажите имя репозитория: ./push_to_github.sh username/repo-name"
    exit 1
fi

REPO_NAME=$1

echo "🚀 Загрузка в GitHub репозиторий: $REPO_NAME"

# Проверяем наличие remote
if git remote get-url origin &>/dev/null; then
    echo "🔄 Обновление remote origin..."
    git remote set-url origin "https://github.com/$REPO_NAME.git"
else
    echo "📝 Добавление remote origin..."
    git remote add origin "https://github.com/$REPO_NAME.git"
fi

echo "📤 Загрузка кода в GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ Успешно загружено в GitHub!"
    echo ""
    echo "🔗 Ссылка на подписку будет:"
    echo "https://raw.githubusercontent.com/$REPO_NAME/main/subscription.txt"
    echo ""
    echo "📝 GitHub Actions будет автоматически обновлять конфиги каждый час"
else
    echo "❌ Ошибка при загрузке. Убедитесь что:"
    echo "   1. Репозиторий создан на GitHub"
    echo "   2. Вы авторизованы в GitHub"
    echo "   3. У вас есть права на запись в репозиторий"
fi


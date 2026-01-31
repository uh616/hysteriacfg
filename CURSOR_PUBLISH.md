# 🚀 Публикация через Cursor

## Способ 1: Через Source Control панель (рекомендуется)

1. **Откройте Source Control:**
   - Нажмите `Ctrl+Shift+G` или кликните на иконку Source Control в боковой панели

2. **Опубликуйте репозиторий:**
   - Нажмите на кнопку **"Publish to GitHub"** или **"..."** → **"Publish Branch"**
   - Выберите имя репозитория (например: `hysteria2-configs`)
   - Выберите видимость (Public/Private)
   - Нажмите **"Publish"**

3. **Готово!** Cursor автоматически:
   - Создаст репозиторий на GitHub
   - Загрузит весь код
   - Настроит remote

## Способ 2: Через терминал (если знаете имя репозитория)

После создания репозитория на GitHub через веб-интерфейс:

```powershell
git remote add origin https://github.com/ваш-username/hysteria2-configs.git
git push -u origin main
```

## После публикации

GitHub Actions автоматически запустится и:
- Проверит конфиги
- Создаст `subscription.txt`
- Обновит `README.md`
- Будет обновляться каждый час

Ссылка на подписку:
```
https://raw.githubusercontent.com/ваш-username/hysteria2-configs/main/subscription.txt
```


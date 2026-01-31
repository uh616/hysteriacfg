# Скрипт для загрузки в GitHub
# Использование: .\push_to_github.ps1 -RepoName "your-username/hysteria2-configs"

param(
    [Parameter(Mandatory=$true)]
    [string]$RepoName
)

Write-Host "🚀 Загрузка в GitHub репозиторий: $RepoName" -ForegroundColor Green

# Проверяем наличие remote
$remoteExists = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "📝 Добавление remote origin..." -ForegroundColor Yellow
    git remote add origin "https://github.com/$RepoName.git"
} else {
    Write-Host "🔄 Обновление remote origin..." -ForegroundColor Yellow
    git remote set-url origin "https://github.com/$RepoName.git"
}

Write-Host "📤 Загрузка кода в GitHub..." -ForegroundColor Yellow
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Успешно загружено в GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔗 Ссылка на подписку будет:" -ForegroundColor Cyan
    Write-Host "https://raw.githubusercontent.com/$RepoName/main/subscription.txt" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📝 GitHub Actions будет автоматически обновлять конфиги каждый час" -ForegroundColor Yellow
} else {
    Write-Host "❌ Ошибка при загрузке. Убедитесь что:" -ForegroundColor Red
    Write-Host "   1. Репозиторий создан на GitHub" -ForegroundColor Red
    Write-Host "   2. Вы авторизованы в GitHub" -ForegroundColor Red
    Write-Host "   3. У вас есть права на запись в репозиторий" -ForegroundColor Red
}


// Конфигурация
const REPO_NAME = 'uh616/REBORNCFG';
const BRANCH = 'main';
const PROTOCOLS = ['hysteria2', 'vless', 'vmess', 'shadowsocks', 'trojan'];
const PROTOCOL_NAMES = {
    'hysteria2': '🚀 Hysteria2',
    'vless': '⚡ VLESS',
    'vmess': '🔷 VMESS',
    'shadowsocks': '🔰 Shadowsocks',
    'trojan': '🎯 Trojan'
};

// Состояние
let allConfigs = [];
let filteredConfigs = [];
let currentFilter = 'all';
let currentTab = 'lists';

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initFilters();
    initSearch();
    loadConfigs();
});

// Инициализация табов
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(`${tab}Tab`).classList.add('active');
            
            currentTab = tab;
        });
    });
}

// Инициализация фильтров
function initFilters() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            currentFilter = btn.dataset.filter;
            applyFilters();
        });
    });
}

// Инициализация поиска
function initSearch() {
    const searchInput = document.getElementById('searchInput');
    
    searchInput.addEventListener('input', (e) => {
        applyFilters();
    });
}

// Загрузка конфигов
async function loadConfigs() {
    const loading = document.getElementById('loading');
    const grid = document.getElementById('configsGrid');
    
    loading.style.display = 'block';
    grid.innerHTML = '';
    
    try {
        allConfigs = [];
        let configId = 1;
        
        // Загружаем конфиги для каждого протокола
        for (const protocol of PROTOCOLS) {
            // Основные подписки (best-1, best-2, best-3)
            for (let i = 1; i <= 3; i++) {
                const url = `https://raw.githubusercontent.com/${REPO_NAME}/${BRANCH}/${protocol}/best-${i}.txt`;
                try {
                    const response = await fetch(url);
                    if (response.ok) {
                        allConfigs.push({
                            id: configId++,
                            protocol: protocol,
                            protocolName: PROTOCOL_NAMES[protocol],
                            url: url,
                            type: 'recommended',
                            name: `${PROTOCOL_NAMES[protocol]} Best-${i}`
                        });
                    }
                } catch (e) {
                    console.error(`Ошибка загрузки ${url}:`, e);
                }
            }
            
            // Основная подписка
            const mainUrl = `https://raw.githubusercontent.com/${REPO_NAME}/${BRANCH}/${protocol}/subscription.txt`;
            try {
                const response = await fetch(mainUrl);
                if (response.ok) {
                    allConfigs.push({
                        id: configId++,
                        protocol: protocol,
                        protocolName: PROTOCOL_NAMES[protocol],
                        url: mainUrl,
                        type: 'main',
                        name: `${PROTOCOL_NAMES[protocol]} Все конфиги`
                    });
                }
            } catch (e) {
                console.error(`Ошибка загрузки ${mainUrl}:`, e);
            }
        }
        
        loading.style.display = 'none';
        applyFilters();
    } catch (error) {
        console.error('Ошибка загрузки конфигов:', error);
        loading.textContent = 'Ошибка загрузки конфигов';
    }
}

// Применение фильтров
function applyFilters() {
    const searchInput = document.getElementById('searchInput');
    const searchTerm = searchInput.value.toLowerCase();
    
    filteredConfigs = allConfigs.filter(config => {
        // Фильтр по типу
        if (currentFilter !== 'all' && currentFilter !== 'recommended') {
            if (config.protocol !== currentFilter) return false;
        }
        
        if (currentFilter === 'recommended' && config.type !== 'recommended') {
            return false;
        }
        
        // Поиск
        if (searchTerm) {
            const searchIn = `${config.protocolName} ${config.name} ${config.protocol}`.toLowerCase();
            if (!searchIn.includes(searchTerm)) return false;
        }
        
        return true;
    });
    
    renderConfigs();
}

// Отрисовка конфигов
function renderConfigs() {
    const grid = document.getElementById('configsGrid');
    const emptyState = document.getElementById('emptyState');
    
    if (filteredConfigs.length === 0) {
        grid.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    grid.style.display = 'grid';
    emptyState.style.display = 'none';
    
    grid.innerHTML = filteredConfigs.map(config => `
        <div class="config-card">
            <div class="config-header">
                <div class="config-id">#${config.id}</div>
                <div class="config-badges">
                    ${config.type === 'recommended' ? '<span class="badge recommended">⭐ Рекомендованный</span>' : ''}
                    <span class="badge protocol">${config.protocolName}</span>
                </div>
            </div>
            <div class="config-url">${config.url}</div>
            <div class="config-time">${new Date().toLocaleString('ru-RU')}</div>
            <button class="copy-btn" onclick="copyConfig('${config.url.replace(/'/g, "\\'")}')">
                📋 Копировать ссылку
            </button>
        </div>
    `).join('');
}

// Копирование конфига
function copyConfig(url) {
    navigator.clipboard.writeText(url).then(() => {
        showToast('✅ Ссылка скопирована!');
    }).catch(() => {
        // Fallback для старых браузеров
        const textarea = document.createElement('textarea');
        textarea.value = url;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('✅ Ссылка скопирована!');
    });
}

// Копирование TON адреса
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('✅ Адрес скопирован!');
    }).catch(() => {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('✅ Адрес скопирован!');
    });
}

// Показ уведомления
function showToast(message) {
    let toast = document.querySelector('.toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    
    toast.textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}


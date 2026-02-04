// Конфигурация
const REPO_NAME = 'uh616/REBORNCFG';
const BRANCH = 'main';
const PROTOCOLS = ['hysteria2', 'vless', 'vmess', 'shadowsocks', 'trojan'];
function getProtocolNames() {
    const langData = translations[currentLang] || translations.ru;
    return {
        'hysteria2': langData.hysteria2,
        'vless': langData.vless,
        'vmess': langData.vmess,
        'shadowsocks': langData.shadowsocks,
        'trojan': langData.trojan
    };
}

// Состояние
let allConfigs = [];
let filteredConfigs = [];
let currentFilter = 'all';
let currentTab = 'lists';
let currentLang = localStorage.getItem('lang') || 'ru';

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    initLanguage();
    initTabs();
    initFilters();
    initSearch();
    loadConfigs();
});

// Инициализация языка
function initLanguage() {
    // Устанавливаем язык из localStorage или по умолчанию ru
    currentLang = localStorage.getItem('lang') || 'ru';
    document.getElementById('htmlLang').setAttribute('lang', currentLang);
    
    // Обновляем заголовок страницы
    updatePageTitle();
    
    // Обновляем переводы
    updateTranslations();
    
    // Инициализируем переключатель языков
    const langBtns = document.querySelectorAll('.lang-btn');
    langBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const lang = btn.dataset.lang;
            currentLang = lang;
            localStorage.setItem('lang', lang);
            document.getElementById('htmlLang').setAttribute('lang', lang);
            
            // Обновляем активную кнопку
            langBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Обновляем заголовок страницы
            updatePageTitle();
            
            // Обновляем переводы
            updateTranslations();
        });
        
        // Устанавливаем активную кнопку
        if (btn.dataset.lang === currentLang) {
            btn.classList.add('active');
        }
    });
}

// Обновление переводов
function updateTranslations() {
    const langData = translations[currentLang];
    if (!langData) return;
    
    // Обновляем элементы с data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (langData[key]) {
            el.textContent = langData[key];
        }
    });
    
    // Обновляем placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (langData[key]) {
            el.placeholder = langData[key];
        }
    });
    
    // Обновляем названия протоколов в фильтрах
    const protocolNames = {
        'hysteria2': langData.hysteria2,
        'vless': langData.vless,
        'vmess': langData.vmess,
        'shadowsocks': langData.shadowsocks,
        'trojan': langData.trojan
    };
    
    document.querySelectorAll('.filter-btn[data-filter]').forEach(btn => {
        const filter = btn.dataset.filter;
        if (filter !== 'all' && filter !== 'recommended' && protocolNames[filter]) {
            btn.textContent = protocolNames[filter];
        }
    });
    
    // Обновляем конфиги если они уже загружены
    if (allConfigs.length > 0) {
        renderConfigs();
    }
}

// Обновление заголовка страницы
function updatePageTitle() {
    if (currentLang === 'en') {
        document.title = '⚡ REBORN CFG - Automatic VPN configs';
    } else {
        document.title = '⚡ REBORN CFG - Автоматические VPN конфиги';
    }
}

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
        const PROTOCOL_NAMES = getProtocolNames();
        const langData = translations[currentLang] || translations.ru;
        
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
                        name: `${PROTOCOL_NAMES[protocol]} ${langData.allConfigs}`
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
        const langData = translations[currentLang] || translations.ru;
        loading.textContent = langData.loading || 'Ошибка загрузки конфигов';
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
    const langData = translations[currentLang] || translations.ru;
    
    if (filteredConfigs.length === 0) {
        grid.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    grid.style.display = 'grid';
    emptyState.style.display = 'none';
    
    const locale = currentLang === 'en' ? 'en-US' : 'ru-RU';
    
    grid.innerHTML = filteredConfigs.map(config => `
        <div class="config-card">
            <div class="config-header">
                <div class="config-id">#${config.id}</div>
                <div class="config-badges">
                    ${config.type === 'recommended' ? `<span class="badge recommended">${langData.recommendedBadge}</span>` : ''}
                    <span class="badge protocol">${config.protocolName}</span>
                </div>
            </div>
            <div class="config-url">${config.url}</div>
            <div class="config-time">${new Date().toLocaleString(locale)}</div>
            <button class="copy-btn" onclick="copyConfig('${config.url.replace(/'/g, "\\'")}')">
                ${langData.copyLink}
            </button>
        </div>
    `).join('');
}

// Копирование конфига
function copyConfig(url) {
    const langData = translations[currentLang] || translations.ru;
    navigator.clipboard.writeText(url).then(() => {
        showToast(langData.linkCopied);
    }).catch(() => {
        // Fallback для старых браузеров
        const textarea = document.createElement('textarea');
        textarea.value = url;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast(langData.linkCopied);
    });
}

// Копирование TON адреса
function copyToClipboard(text) {
    const langData = translations[currentLang] || translations.ru;
    navigator.clipboard.writeText(text).then(() => {
        showToast(langData.addressCopied);
    }).catch(() => {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast(langData.addressCopied);
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


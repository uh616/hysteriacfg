// Конфигурация
const REPO_NAME = 'uh616/REBORNCFG';
const BRANCH = 'main';
const PROTOCOLS = ['hysteria2', 'vless', 'vmess', 'shadowsocks', 'trojan'];

// Кэш (чтобы не ждать каждый раз проверки 20 ссылок)
const CONFIGS_CACHE_KEY = 'reborncfg:configs:v1';
const CONFIGS_CACHE_TTL_MS = 60 * 60 * 1000; // 1 час
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
let configItems = []; // базовые данные (без текстов), чтобы правильно переименовывать при смене языка
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

function nowMs() {
    return Date.now();
}

function readConfigsCache() {
    try {
        const raw = localStorage.getItem(CONFIGS_CACHE_KEY);
        if (!raw) return null;
        const parsed = JSON.parse(raw);
        if (!parsed || typeof parsed !== 'object') return null;
        if (!Array.isArray(parsed.items)) return null;
        if (typeof parsed.savedAt !== 'number') return null;
        return parsed;
    } catch {
        return null;
    }
}

function writeConfigsCache(items) {
    try {
        localStorage.setItem(
            CONFIGS_CACHE_KEY,
            JSON.stringify({
                savedAt: nowMs(),
                items
            })
        );
    } catch {
        // ignore (storage может быть переполнен/запрещён)
    }
}

function isCacheFresh(cache) {
    if (!cache) return false;
    return nowMs() - cache.savedAt < CONFIGS_CACHE_TTL_MS;
}

function buildDisplayConfigs(items) {
    const PROTOCOL_NAMES = getProtocolNames();
    const langData = translations[currentLang] || translations.ru;

    let configId = 1;
    return items.map(item => {
        const protocolName = PROTOCOL_NAMES[item.protocol] || item.protocol;
        let name = '';
        if (item.type === 'recommended') {
            name = `${protocolName} Best-${item.bestIndex}`;
        } else {
            name = `${protocolName} ${langData.allConfigs}`;
        }

        return {
            id: configId++,
            protocol: item.protocol,
            protocolName,
            url: item.url,
            type: item.type,
            name
        };
    });
}

function createLinkPlan() {
    const items = [];
    for (const protocol of PROTOCOLS) {
        for (let i = 1; i <= 3; i++) {
            items.push({
                protocol,
                type: 'recommended',
                bestIndex: i,
                url: `https://raw.githubusercontent.com/${REPO_NAME}/${BRANCH}/${protocol}/best-${i}.txt`
            });
        }

        items.push({
            protocol,
            type: 'main',
            url: `https://raw.githubusercontent.com/${REPO_NAME}/${BRANCH}/${protocol}/subscription.txt`
        });
    }
    return items;
}

async function fetchWithTimeout(url, { method = 'GET', cache = 'no-store' } = {}, timeoutMs = 2500) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(url, {
            method,
            cache,
            signal: controller.signal
        });
        return response;
    } finally {
        clearTimeout(timeoutId);
    }
}

async function checkUrlExists(url) {
    // HEAD быстрее и не качает файл целиком
    try {
        const head = await fetchWithTimeout(url, { method: 'HEAD', cache: 'no-store' }, 2500);
        if (head.ok) return true;
        if (head.status === 404) return false;
    } catch {
        // ignore
    }

    // fallback: GET (если HEAD вдруг не проходит)
    try {
        const get = await fetchWithTimeout(url, { method: 'GET', cache: 'no-store' }, 2500);
        return get.ok;
    } catch {
        return false;
    }
}

async function mapWithConcurrency(items, mapper, concurrency = 8) {
    const results = new Array(items.length);
    let i = 0;

    async function worker() {
        while (true) {
            const idx = i++;
            if (idx >= items.length) return;
            results[idx] = await mapper(items[idx], idx);
        }
    }

    const workers = Array.from({ length: Math.min(concurrency, items.length) }, () => worker());
    await Promise.all(workers);
    return results;
}

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
    
    // Обновляем конфиги если они уже загружены (пересобираем тексты под выбранный язык)
    if (configItems.length > 0) {
        allConfigs = buildDisplayConfigs(configItems);
        applyFilters();
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
        const cache = readConfigsCache();
        const planned = createLinkPlan();

        // 1) Если кэш свежий — показываем сразу, а обновляем тихо в фоне
        if (isCacheFresh(cache)) {
            configItems = cache.items;
            allConfigs = buildDisplayConfigs(configItems);
            loading.style.display = 'none';
            applyFilters();

            // Фоновое обновление: если список изменился — перерисуем и перезапишем кэш
            void refreshConfigs(planned, { silent: true });
            return;
        }

        // 2) Если кэша нет/просрочен — грузим с проверкой существования ссылок (параллельно)
        await refreshConfigs(planned, { silent: false });
    } catch (error) {
        console.error('Ошибка загрузки конфигов:', error);
        const langData = translations[currentLang] || translations.ru;
        loading.textContent = langData.loading || 'Ошибка загрузки конфигов';
    }
}

async function refreshConfigs(plannedItems, { silent } = { silent: false }) {
    const loading = document.getElementById('loading');

    if (!silent) {
        loading.style.display = 'block';
    }

    const existsList = await mapWithConcurrency(
        plannedItems,
        async (item) => {
            const exists = await checkUrlExists(item.url);
            return exists ? item : null;
        },
        8
    );

    const existing = existsList.filter(Boolean);

    // Если вдруг GitHub недоступен и ничего не нашли — попробуем хотя бы показать старый кэш (если был)
    if (existing.length === 0) {
        const cache = readConfigsCache();
        if (cache?.items?.length) {
            allConfigs = buildDisplayConfigs(cache.items);
            loading.style.display = 'none';
            applyFilters();
            return;
        }
    }

    // Обновляем состояние и кэш
    writeConfigsCache(existing);

    configItems = existing;
    const nextConfigs = buildDisplayConfigs(configItems);
    const changed = JSON.stringify(nextConfigs.map(c => c.url)) !== JSON.stringify(allConfigs.map(c => c.url));

    allConfigs = nextConfigs;
    loading.style.display = 'none';
    if (!silent || changed) {
        applyFilters();
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


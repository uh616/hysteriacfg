"""
Hysteria2 Config Checker
Скрипт для проверки работоспособности Hysteria2 конфигов
"""

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
import concurrent.futures
import urllib.parse
import threading
import requests

# Попытка импорта zoneinfo с fallback
ZONEINFO_AVAILABLE = False
PYTZ_AVAILABLE = False

try:
    import zoneinfo
    # Проверяем что zoneinfo может работать
    try:
        _ = zoneinfo.ZoneInfo("Europe/Moscow")
        ZONEINFO_AVAILABLE = True
    except Exception:
        # zoneinfo есть, но tzdata не установлен или не работает
        ZONEINFO_AVAILABLE = False
        try:
            import pytz
            PYTZ_AVAILABLE = True
        except ImportError:
            PYTZ_AVAILABLE = False
except ImportError:
    # zoneinfo не доступен, пробуем pytz
    ZONEINFO_AVAILABLE = False
    try:
        import pytz
        PYTZ_AVAILABLE = True
    except ImportError:
        PYTZ_AVAILABLE = False
import urllib3
import base64
import json
import re
import os
import socket
import time

# GitHub API (опционально)
GITHUB_AVAILABLE = False
try:
    from github import Github, Auth
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -------------------- КОНФИГУРАЦИЯ --------------------
CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/143.0.0.0 Safari/537.36"
)

DEFAULT_MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "30"))  # Уменьшено для стабильности
TIMEOUT = 8  # Уменьшено для более быстрой обработки
PING_TIMEOUT = 3  # Уменьшено для быстрой проверки недоступных серверов
SPEED_TEST_DURATION = 3  # Уменьшено для быстрой проверки скорости
MAX_FETCH_TIME = 15  # Максимальное время на один запрос (секунды)

# URL источников конфигов
CONFIG_URLS = [
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/all_configs.txt",
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/all_sub.txt",
    "https://raw.githubusercontent.com/AzadNetCH/Clash/main/AzadNet.txt",
    "https://sub.azadnetch.workers.dev/AzadNetCH/Clash/main/AzadNet.txt",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/all.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server.txt",
    "https://raw.githubusercontent.com/Argh94/V2RayAutoConfig/refs/heads/main/configs/Hysteria2.txt",
    "https://raw.githubusercontent.com/coldwater-10/V2ray-Config/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/WLget/V2Ray_configs_64/master/ConfigSub_list.txt",
    "https://raw.githubusercontent.com/arshiacomplus/v2rayExtractor/refs/heads/main/hy2.html",
    "https://raw.githubusercontent.com/arshiacomplus/v2rayExtractor/refs/heads/main/mix/sub.html",
    "https://raw.githubusercontent.com/nyeinkokoaung404/V2ray-Configs/main/All_Configs_Sub.txt",
    # Новые актуальные источники Hysteria2
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/hysteria2.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/hy2.txt",
    "https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/hysteria2.txt",
    "https://raw.githubusercontent.com/mianfeifq/share/main/data2023113.txt",
    "https://raw.githubusercontent.com/mianfeifq/share/main/data2023114.txt",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/ripaojiedian/freenode/main/sub",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/all",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/hysteria2",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list_raw.txt",
    "https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/free",
    "https://raw.githubusercontent.com/yu-steven/openit/main/sub/hysteria2",
    "https://raw.githubusercontent.com/yu-steven/openit/main/sub/hy2",
    "https://raw.githubusercontent.com/yu-steven/openit/main/sub/mix",
    "https://raw.githubusercontent.com/anaer/Sub/main/sub/hysteria2.txt",
    "https://raw.githubusercontent.com/anaer/Sub/main/sub/hy2.txt",
    "https://raw.githubusercontent.com/anaer/Sub/main/sub/mix.txt",
    "https://raw.githubusercontent.com/iwxf/free-v2ray/main/hysteria2",
    "https://raw.githubusercontent.com/iwxf/free-v2ray/main/hy2",
    "https://raw.githubusercontent.com/clashconfigs/free/main/hysteria2.txt",
    "https://raw.githubusercontent.com/clashconfigs/free/main/hy2.txt",
    "https://raw.githubusercontent.com/clashconfigs/free/main/mix.txt",
    "https://raw.githubusercontent.com/ssrsub/ssr/main/hysteria2",
    "https://raw.githubusercontent.com/ssrsub/ssr/main/hy2",
    "https://raw.githubusercontent.com/ssrsub/ssr/main/mix",
    "https://raw.githubusercontent.com/ProxySU-Open/ProxySU/main/hysteria2.txt",
    "https://raw.githubusercontent.com/ProxySU-Open/ProxySU/main/hy2.txt",
    "https://raw.githubusercontent.com/FreeNode/FreeNode/main/hysteria2",
    "https://raw.githubusercontent.com/FreeNode/FreeNode/main/hy2",
    "https://raw.githubusercontent.com/FreeNode/FreeNode/main/mix",
    "https://raw.githubusercontent.com/v2ray-agent/v2ray-agent/main/config/hysteria2.txt",
    "https://raw.githubusercontent.com/v2ray-agent/v2ray-agent/main/config/hy2.txt",
]

# Дополнительные URL из примера (если нужно)
ADDITIONAL_URLS = [
    "https://github.com/sakha1370/OpenRay/raw/refs/heads/main/output/all_valid_proxies.txt",
    "https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/protocols/vl.txt",
    "https://raw.githubusercontent.com/yitong2333/proxy-minging/refs/heads/main/v2ray.txt",
    "https://raw.githubusercontent.com/acymz/AutoVPN/refs/heads/main/data/V2.txt",
    "https://raw.githubusercontent.com/miladtahanian/V2RayCFGDumper/refs/heads/main/config.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt",
    "https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/trojan.txt",
    "https://raw.githubusercontent.com/YasserDivaR/pr0xy/refs/heads/main/ShadowSocks2021.txt",
    "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/vless.txt",
    "https://raw.githubusercontent.com/mheidari98/.proxy/refs/heads/main/vless",
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt",
    "https://raw.githubusercontent.com/mheidari98/.proxy/refs/heads/main/all",
    "https://github.com/Kwinshadow/TelegramV2rayCollector/raw/refs/heads/main/sublinks/mix.txt",
    "https://github.com/LalatinaHub/Mineral/raw/refs/heads/master/result/nodes",
    "https://raw.githubusercontent.com/miladtahanian/multi-proxy-config-fetcher/refs/heads/main/configs/proxy_configs.txt",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/refs/heads/main/sub",
    "https://github.com/MhdiTaheri/V2rayCollector_Py/raw/refs/heads/main/sub/Mix/mix.txt",
    "https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/vmess.txt",
    "https://github.com/MhdiTaheri/V2rayCollector/raw/refs/heads/main/sub/mix",
    "https://github.com/Argh94/Proxy-List/raw/refs/heads/main/All_Config.txt",
    "https://raw.githubusercontent.com/shabane/kamaji/master/hub/merged.txt",
    "https://raw.githubusercontent.com/wuqb2i4f/xray-config-toolkit/main/output/base64/mix-uri",
    "https://raw.githubusercontent.com/STR97/STRUGOV/refs/heads/main/STR.BYPASS#STR.BYPASS%F0%9F%91%BE",
    "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/refs/heads/main/Config/vless.txt",
]

ALL_URLS = CONFIG_URLS + ADDITIONAL_URLS

# GitHub настройки (можно задать через переменные окружения)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO_NAME = os.environ.get("GITHUB_REPO_NAME", "")  # Формат: username/repo-name
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")

# -------------------- ЛОГИРОВАНИЕ --------------------
LOGS = []
_LOG_LOCK = threading.Lock()

def get_timezone():
    """Получает объект часового пояса с fallback."""
    if ZONEINFO_AVAILABLE:
        try:
            return zoneinfo.ZoneInfo("Europe/Moscow")
        except:
            pass
    
    if PYTZ_AVAILABLE:
        try:
            return pytz.timezone("Europe/Moscow")
        except:
            pass
    
    # Fallback на UTC если ничего не работает
    return None

def log(message: str):
    """Добавляет сообщение в лог потокобезопасно."""
    tz = get_timezone()
    if tz:
        timestamp = datetime.now(tz).strftime("%H:%M:%S")
    else:
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
    with _LOG_LOCK:
        log_msg = f"[{timestamp}] {message}"
        LOGS.append(log_msg)
        print(log_msg)

# -------------------- HTTP СЕССИЯ --------------------
def _build_session(max_pool_size: int) -> requests.Session:
    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=max_pool_size,
        pool_maxsize=max_pool_size,
        max_retries=Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("HEAD", "GET", "OPTIONS"),
        ),
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": CHROME_UA})
    return session

REQUESTS_SESSION = _build_session(max_pool_size=max(DEFAULT_MAX_WORKERS, len(ALL_URLS)))

# -------------------- ЗАГРУЗКА ДАННЫХ --------------------
def fetch_data(url: str, timeout: int = TIMEOUT, max_attempts: int = 2) -> str:
    """Загружает данные по URL с повторными попытками."""
    for attempt in range(1, max_attempts + 1):
        try:
            modified_url = url
            verify = True

            if attempt == 2:
                verify = False
                # Для второй попытки используем более короткий таймаут
                timeout = min(timeout, 5)

            # Используем более короткий таймаут для избежания зависаний
            actual_timeout = min(timeout, MAX_FETCH_TIME)
            
            response = REQUESTS_SESSION.get(modified_url, timeout=actual_timeout, verify=verify)
            response.raise_for_status()
            
            # Ограничиваем размер ответа (максимум 10MB)
            if len(response.content) > 10 * 1024 * 1024:
                log(f"⚠️ Ответ слишком большой от {url}, пропускаем")
                return ""
            
            return response.text

        except requests.exceptions.Timeout:
            if attempt < max_attempts:
                continue
            log(f"⏱️ Таймаут при загрузке {url}")
            return ""
        except requests.exceptions.RequestException as exc:
            if attempt < max_attempts:
                continue
            log(f"⚠️ Ошибка при загрузке {url}: {str(exc)[:100]}")
            return ""
        except Exception as exc:
            if attempt < max_attempts:
                continue
            log(f"⚠️ Неожиданная ошибка при загрузке {url}: {str(exc)[:100]}")
            return ""

# -------------------- ПАРСИНГ КОНФИГОВ --------------------
def extract_hysteria2_configs(data: str) -> list[str]:
    """Извлекает все Hysteria2 конфиги из текста."""
    configs = []
    
    # Удаляем HTML теги если есть
    data = re.sub(r'<[^>]+>', '', data)
    
    # Паттерны для поиска hysteria2:// и hy2://
    patterns = [
        r'hysteria2://[^\s\n<>"\'\)]+',
        r'hy2://[^\s\n<>"\'\)]+',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, data, re.IGNORECASE)
        configs.extend(matches)
    
    # Также ищем в base64 декодированном виде
    try:
        # Пытаемся декодировать base64 (может быть несколько попыток)
        for padding in ['', '=', '==', '===']:
            try:
                decoded = base64.b64decode(data + padding).decode('utf-8', errors='ignore')
                for pattern in patterns:
                    matches = re.findall(pattern, decoded, re.IGNORECASE)
                    configs.extend(matches)
                break
            except:
                continue
    except:
        pass
    
    # Очистка конфигов от лишних символов
    cleaned_configs = []
    for cfg in configs:
        # Убираем возможные артефакты в конце
        cfg = cfg.rstrip('.,;:!?)\'"')
        # Проверяем что это действительно валидный конфиг
        if len(cfg) > 10 and ('://' in cfg):
            cleaned_configs.append(cfg)
    
    # Дедупликация
    unique_configs = list(dict.fromkeys(cleaned_configs))
    return unique_configs

def normalize_config_url(config_url: str) -> str:
    """Нормализует URL конфига для сравнения (убирает лишние параметры, сортирует параметры)."""
    try:
        if not config_url.startswith(('hysteria2://', 'hy2://')):
            return config_url
        
        # Нормализуем префикс
        if config_url.startswith('hy2://'):
            config_url = config_url.replace('hy2://', 'hysteria2://', 1)
        
        # Разделяем на части
        url_part = config_url.split('://', 1)[1]
        
        # Убираем фрагмент (#...)
        if '#' in url_part:
            url_part = url_part.split('#')[0]
        
        # Разделяем на auth@host:port и параметры
        if '@' in url_part:
            auth_part, rest = url_part.split('@', 1)
        else:
            auth_part, rest = None, url_part
        
        # Разделяем host:port и параметры
        if '?' in rest:
            host_port, params_str = rest.split('?', 1)
        else:
            host_port, params_str = rest, ""
        
        # Нормализуем host:port (убираем лишние пробелы, приводим к нижнему регистру)
        host_port = host_port.strip().lower()
        
        # Парсим и сортируем параметры для единообразия
        params = {}
        if params_str:
            for param in params_str.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    key = key.strip().lower()
                    value = urllib.parse.unquote(value).strip()
                    # Игнорируем некоторые параметры которые не влияют на уникальность
                    if key not in ['remarks', 'name', 'description', 'tag']:
                        params[key] = value
        
        # Собираем обратно
        normalized = f"hysteria2://"
        if auth_part:
            normalized += f"{auth_part}@"
        normalized += host_port
        if params:
            sorted_params = sorted(params.items())
            param_str = '&'.join([f"{k}={urllib.parse.quote(v)}" for k, v in sorted_params])
            normalized += f"?{param_str}"
        
        return normalized
    except Exception:
        return config_url

def deduplicate_configs(configs: list[str], show_log: bool = True) -> list[str]:
    """Умная дедупликация конфигов по host:port и полному URL."""
    seen_full = set()  # Полные нормализованные URL
    seen_hostport = set()  # host:port для проверки дубликатов
    unique_configs = []
    duplicates_full = 0  # Дубликаты по полному URL
    duplicates_hostport = 0  # Дубликаты по host:port
    
    for config in configs:
        config = config.strip()
        if not config:
            continue
        
        # Нормализуем URL
        normalized = normalize_config_url(config)
        
        # Проверяем полное совпадение
        if normalized in seen_full:
            duplicates_full += 1
            continue
        
        # Парсим для проверки host:port
        parsed = parse_hysteria2_url(config)
        if parsed:
            host = parsed['host'].lower().strip()
            port = parsed['port']
            hostport_key = f"{host}:{port}"
            
            # Проверяем дубликат по host:port
            if hostport_key in seen_hostport:
                duplicates_hostport += 1
                continue
            
            seen_hostport.add(hostport_key)
        else:
            # Если не удалось распарсить, все равно добавляем в seen_full
            pass
        
        seen_full.add(normalized)
        unique_configs.append(config)
    
    total_duplicates = duplicates_full + duplicates_hostport
    if total_duplicates > 0 and show_log:
        if duplicates_full > 0:
            log(f"🔍 Удалено {duplicates_full} полных дубликатов")
        if duplicates_hostport > 0:
            log(f"🔍 Удалено {duplicates_hostport} дубликатов по host:port")
    
    return unique_configs

def parse_hysteria2_url(config_url: str) -> dict:
    """Парсит Hysteria2 URL и извлекает параметры."""
    try:
        # Нормализуем префикс
        if config_url.startswith('hy2://'):
            config_url = config_url.replace('hy2://', 'hysteria2://', 1)
        
        if not config_url.startswith('hysteria2://'):
            return None
        
        # Убираем префикс и возможные фрагменты
        url_part = config_url.split('://', 1)[1]
        # Убираем фрагмент (#...) если есть
        if '#' in url_part:
            url_part = url_part.split('#')[0]
        
        # Разделяем на части (auth@host:port?params)
        # Ищем последний @ перед параметрами
        if '@' in url_part:
            # Разделяем по @, но учитываем что IPv6 может содержать ::
            parts = url_part.split('@')
            if len(parts) == 2:
                auth_part, rest = parts
            else:
                # Может быть несколько @, берем последний
                auth_part = '@'.join(parts[:-1])
                rest = parts[-1]
        else:
            auth_part, rest = None, url_part
        
        # Разделяем host:port и параметры
        if '?' in rest:
            host_port, params_str = rest.split('?', 1)
        else:
            host_port, params_str = rest, ""
        
        # Парсим host:port (учитываем IPv6)
        host = None
        port = 443
        
        if '[' in host_port and ']' in host_port:
            # IPv6 формат [host]:port
            match = re.match(r'\[([^\]]+)\]:(\d+)', host_port)
            if match:
                host = match.group(1)
                port = int(match.group(2))
            else:
                # Попытка без порта
                host = host_port.strip('[]')
        elif ':' in host_port:
            # Обычный формат host:port или IPv6 без скобок
            # Считаем что последний : это разделитель порта
            last_colon = host_port.rfind(':')
            if last_colon > 0:
                potential_host = host_port[:last_colon]
                potential_port = host_port[last_colon+1:]
                # Проверяем что после : это число
                if potential_port.isdigit():
                    host = potential_host
                    port = int(potential_port)
                else:
                    # Возможно это IPv6 без скобок
                    host = host_port
            else:
                host = host_port
        else:
            host = host_port
        
        if not host:
            return None
        
        # Парсим параметры
        params = {}
        if params_str:
            for param in params_str.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = urllib.parse.unquote(value)
        
        return {
            'host': host.strip(),
            'port': port,
            'auth': auth_part,
            'params': params,
            'original': config_url
        }
    except Exception as e:
        return None

# -------------------- ПРОВЕРКА ПИНГА --------------------
def check_ping(host: str, port: int, timeout: int = PING_TIMEOUT) -> float | None:
    """Проверяет доступность хоста через TCP соединение."""
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            ping_time = (time.time() - start_time) * 1000  # в миллисекундах
            return round(ping_time, 2)
        return None
    except socket.timeout:
        return None
    except Exception:
        return None

# -------------------- ОПРЕДЕЛЕНИЕ СТРАНЫ --------------------
_COUNTRY_CACHE = {}
_COUNTRY_CACHE_LOCK = threading.Lock()

def get_country_by_ip(host: str, use_cache: bool = True) -> str:
    """Определяет страну по IP адресу с кэшированием и несколькими API."""
    # Проверяем кэш
    if use_cache:
        with _COUNTRY_CACHE_LOCK:
            if host in _COUNTRY_CACHE:
                return _COUNTRY_CACHE[host]
    
    try:
        # Пытаемся получить IP из хоста
        ip = None
        try:
            ip = socket.gethostbyname(host)
        except:
            # Если это уже IP
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', host):
                ip = host
            else:
                # Пробуем еще раз с большим таймаутом
                try:
                    socket.setdefaulttimeout(5)
                    ip = socket.gethostbyname(host)
                except:
                    pass
        
        if not ip:
            country = "Unknown"
            if use_cache:
                with _COUNTRY_CACHE_LOCK:
                    _COUNTRY_CACHE[host] = country
            return country
        
        # Пробуем несколько API для определения страны
        apis = [
            # ip-api.com (бесплатный, до 45 запросов/минуту)
            (f"http://ip-api.com/json/{ip}?fields=country", "country", 5),
            # ipapi.co (бесплатный, до 1000 запросов/день)
            (f"https://ipapi.co/{ip}/country_name/", None, 5),
            # ip-api.com с другим форматом
            (f"https://ip-api.com/json/{ip}?fields=country", "country", 5),
        ]
        
        for api_url, json_key, timeout in apis:
            try:
                response = REQUESTS_SESSION.get(api_url, timeout=timeout)
                if response.status_code == 200:
                    if json_key:
                        # JSON ответ
                        data = response.json()
                        country = data.get(json_key, '').strip()
                        if country and country != 'Unknown' and country != '':
                            if use_cache:
                                with _COUNTRY_CACHE_LOCK:
                                    _COUNTRY_CACHE[host] = country
                            return country
                    else:
                        # Текстовый ответ
                        country = response.text.strip()
                        if country and country != 'Unknown' and country != '' and len(country) < 100:
                            if use_cache:
                                with _COUNTRY_CACHE_LOCK:
                                    _COUNTRY_CACHE[host] = country
                            return country
            except:
                continue
        
        # Если все API не сработали, пробуем еще раз с ip-api.com (основной)
        try:
            response = REQUESTS_SESSION.get(
                f"http://ip-api.com/json/{ip}?fields=country,status",
                timeout=8
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    country = data.get('country', 'Unknown')
                    if country and country != 'Unknown':
                        if use_cache:
                            with _COUNTRY_CACHE_LOCK:
                                _COUNTRY_CACHE[host] = country
                        return country
        except:
            pass
        
        country = "Unknown"
        if use_cache:
            with _COUNTRY_CACHE_LOCK:
                _COUNTRY_CACHE[host] = country
        return country
    except Exception as e:
        country = "Unknown"
        if use_cache:
            with _COUNTRY_CACHE_LOCK:
                _COUNTRY_CACHE[host] = country
        return country

def get_countries_for_configs(configs: list[str]) -> dict[str, list[str]]:
    """Определяет страны для всех конфигов и группирует их."""
    configs_by_country = {}
    total = len(configs)
    processed = 0
    
    def process_config(config):
        nonlocal processed
        try:
            parsed = parse_hysteria2_url(config)
            if not parsed:
                return None, "Unknown"
            
            host = parsed['host']
            country = get_country_by_ip(host)
            processed += 1
            
            if processed % 50 == 0:
                log(f"🌍 Определение стран: {processed}/{total} ({processed*100//total}%)")
            
            return config, country
        except:
            processed += 1
            return None, "Unknown"
    
    log(f"🌍 Определение стран для {total} конфигов...")
    
    # Используем параллельную обработку для определения стран
    # Уменьшаем количество воркеров чтобы не превысить лимиты API (45 запросов/минуту для ip-api.com)
    max_workers = min(10, total)  # Уменьшено с 20 до 10
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_config, config) for config in configs]
        for future in concurrent.futures.as_completed(futures):
            try:
                config, country = future.result(timeout=15)  # Увеличено с 10 до 15
                if config:
                    if country not in configs_by_country:
                        configs_by_country[country] = []
                    configs_by_country[country].append(config)
            except:
                pass
    
    log(f"✅ Определение стран завершено: найдено {len(configs_by_country)} стран")
    return configs_by_country

# -------------------- ПРОВЕРКА СКОРОСТИ --------------------
def test_speed(host: str, port: int, timeout: int = SPEED_TEST_DURATION) -> dict:
    """Тестирует скорость соединения (упрощенная версия)."""
    try:
        # Простая проверка: измеряем время передачи данных
        start_time = time.time()
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        try:
            connect_start = time.time()
            sock.connect((host, port))
            connect_time = time.time() - connect_start
            
            # Пытаемся отправить и получить данные
            try:
                test_data = b'GET / HTTP/1.1\r\nHost: ' + host.encode() + b'\r\nConnection: close\r\n\r\n'
                send_start = time.time()
                sock.send(test_data)
                sock.recv(4096)
                transfer_time = time.time() - send_start
                total_time = time.time() - start_time
                
                # Оценка скорости на основе времени соединения и передачи
                if connect_time < 0.3 and total_time < 0.8:
                    estimated_speed = "Very High"
                elif connect_time < 0.5 and total_time < 1.5:
                    estimated_speed = "High"
                elif connect_time < 1.0 and total_time < 2.5:
                    estimated_speed = "Medium"
                else:
                    estimated_speed = "Low"
                
                sock.close()
                
                return {
                    'speed': estimated_speed,
                    'connection_time': round(connect_time, 3),
                    'transfer_time': round(transfer_time, 3),
                    'total_time': round(total_time, 3)
                }
            except:
                sock.close()
                # Если соединение установлено, но передача не удалась
                if connect_time < 0.5:
                    return {'speed': 'Medium', 'connection_time': round(connect_time, 3), 'transfer_time': None, 'total_time': round(connect_time, 3)}
                else:
                    return {'speed': 'Low', 'connection_time': round(connect_time, 3), 'transfer_time': None, 'total_time': round(connect_time, 3)}
        except socket.timeout:
            sock.close()
            return {'speed': 'Failed', 'connection_time': None, 'transfer_time': None, 'total_time': None}
        except:
            sock.close()
            return {'speed': 'Failed', 'connection_time': None, 'transfer_time': None, 'total_time': None}
    except Exception as e:
        return {'speed': 'Failed', 'connection_time': None, 'transfer_time': None, 'total_time': None}

# -------------------- ВАЛИДАЦИЯ КОНФИГА --------------------
def validate_hysteria2_config(config_url: str) -> bool:
    """Проверяет что конфиг валиден для Hysteria2."""
    try:
        parsed = parse_hysteria2_url(config_url)
        if not parsed:
            return False
        
        # Проверяем обязательные параметры
        host = parsed['host']
        port = parsed['port']
        auth = parsed.get('auth')
        params = parsed.get('params', {})
        
        # Хост не должен быть пустым
        if not host or len(host.strip()) == 0:
            return False
        
        # Порт должен быть валидным
        if port < 1 or port > 65535:
            return False
        
        # Auth должен быть (для Hysteria2 это обязательно)
        if not auth or len(auth.strip()) == 0:
            return False
        
        # Проверяем что нет небезопасных параметров
        decoded = urllib.parse.unquote(config_url.lower())
        if 'insecure=1' in decoded or 'allowinsecure=1' in decoded:
            return False
        
        # Проверяем формат хоста (должен быть IP или домен)
        # Разрешаем IP, домены и IPv6 в скобках
        host_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$|^\d+\.\d+\.\d+\.\d+$|^\[([0-9a-fA-F:]+)\]$'
        if not re.match(host_pattern, host):
            return False
        
        # Проверяем что auth не содержит недопустимых символов
        if auth:
            # Auth должен быть валидным (не пустым и не слишком длинным)
            if len(auth) < 4 or len(auth) > 200:
                return False
        
        return True
    except Exception:
        return False

# -------------------- ПРОВЕРКА КОНФИГА --------------------
def check_config(config_url: str) -> dict:
    """Проверяет один конфиг на работоспособность."""
    # Сначала валидируем конфиг
    if not validate_hysteria2_config(config_url):
        return None
    
    parsed = parse_hysteria2_url(config_url)
    if not parsed:
        return None
    
    host = parsed['host']
    port = parsed['port']
    
    # Проверяем ping (более строгая проверка)
    ping = check_ping(host, port)
    if ping is None:
        return None  # Сервер недоступен
    
    # Дополнительная проверка: пытаемся установить соединение и отправить данные
    # Это более надежная проверка чем просто ping
    if not test_hysteria2_connection(host, port):
        return None  # Не удалось установить соединение
    
    # Определяем страну
    country = get_country_by_ip(host)
    
    # Проверяем скорость (упрощенная)
    speed_info = test_speed(host, port)
    
    return {
        'config': config_url,
        'host': host,
        'port': port,
        'ping': ping,
        'country': country,
        'speed': speed_info['speed'],
        'connection_time': speed_info.get('connection_time'),
        'transfer_time': speed_info.get('transfer_time'),
        'total_time': speed_info.get('total_time')
    }

def test_hysteria2_connection(host: str, port: int, timeout: int = 4) -> bool:
    """Проверяет что можно установить соединение с Hysteria2 сервером."""
    try:
        # Hysteria2 использует QUIC (UDP), но мы проверяем что порт доступен через TCP
        # Это базовая проверка доступности
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Пытаемся подключиться
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result != 0:
            return False
        
        # Дополнительная проверка: пытаемся еще раз с небольшим интервалом
        # Это помогает отфильтровать нестабильные соединения
        time.sleep(0.1)
        sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock2.settimeout(timeout)
        result2 = sock2.connect_ex((host, port))
        sock2.close()
        
        return result2 == 0
    except Exception:
        return False

# -------------------- ФИЛЬТРАЦИЯ НЕБЕЗОПАСНЫХ КОНФИГОВ --------------------
INSECURE_PATTERN = re.compile(
    r'(?:[?&;]|3%[Bb])(allowinsecure|allow_insecure|insecure)=(?:1|true|yes)(?:[&;#]|$|(?=\s|$))',
    re.IGNORECASE
)

def filter_insecure_configs(configs: list[str]) -> list[str]:
    """Фильтрует конфиги с insecure=1 или allowInsecure=1."""
    safe_configs = []
    filtered_count = 0
    
    for config in configs:
        # Декодируем URL для проверки
        decoded = urllib.parse.unquote(config)
        
        # Проверяем на наличие insecure параметров
        if INSECURE_PATTERN.search(decoded):
            filtered_count += 1
            continue
        
        safe_configs.append(config)
    
    if filtered_count > 0:
        log(f"🔒 Отфильтровано {filtered_count} небезопасных конфигов (insecure=1)")
    
    return safe_configs

# -------------------- GITHUB ФУНКЦИИ --------------------
def create_subscription_file(configs: list[str], filename: str = "subscription.txt") -> str:
    """Создает файл подписки со всеми Hysteria2 конфигами."""
    subscription_content = "\n".join(configs)
    
    # Сохраняем локально
    with open(filename, "w", encoding="utf-8") as f:
        f.write(subscription_content)
    
    log(f"📝 Создан файл подписки: {filename} ({len(configs)} конфигов)")
    return filename

def get_country_flag_emoji(country: str) -> str:
    """Возвращает эмодзи флага для страны."""
    # Расширенный список стран с эмодзи флагами
    flags = {
        "United States": "🇺🇸", "US": "🇺🇸",
        "Russia": "🇷🇺", "RU": "🇷🇺",
        "China": "🇨🇳", "CN": "🇨🇳",
        "Japan": "🇯🇵", "JP": "🇯🇵",
        "South Korea": "🇰🇷", "KR": "🇰🇷",
        "Germany": "🇩🇪", "DE": "🇩🇪",
        "United Kingdom": "🇬🇧", "GB": "🇬🇧",
        "France": "🇫🇷", "FR": "🇫🇷",
        "Singapore": "🇸🇬", "SG": "🇸🇬",
        "Netherlands": "🇳🇱", "NL": "🇳🇱",
        "Canada": "🇨🇦", "CA": "🇨🇦",
        "Australia": "🇦🇺", "AU": "🇦🇺",
        "India": "🇮🇳", "IN": "🇮🇳",
        "Brazil": "🇧🇷", "BR": "🇧🇷",
        "Turkey": "🇹🇷", "TR": "🇹🇷",
        "Italy": "🇮🇹", "IT": "🇮🇹",
        "Spain": "🇪🇸", "ES": "🇪🇸",
        "Sweden": "🇸🇪", "SE": "🇸🇪",
        "Switzerland": "🇨🇭", "CH": "🇨🇭",
        "Poland": "🇵🇱", "PL": "🇵🇱",
        "Ukraine": "🇺🇦", "UA": "🇺🇦",
        "Taiwan": "🇹🇼", "TW": "🇹🇼",
        "Hong Kong": "🇭🇰", "HK": "🇭🇰",
        "Thailand": "🇹🇭", "TH": "🇹🇭",
        "Vietnam": "🇻🇳", "VN": "🇻🇳",
        "Indonesia": "🇮🇩", "ID": "🇮🇩",
        "Malaysia": "🇲🇾", "MY": "🇲🇾",
        "Philippines": "🇵🇭", "PH": "🇵🇭",
        "Israel": "🇮🇱", "IL": "🇮🇱",
        "Saudi Arabia": "🇸🇦", "SA": "🇸🇦",
        "United Arab Emirates": "🇦🇪", "AE": "🇦🇪",
        "Egypt": "🇪🇬", "EG": "🇪🇬",
        "South Africa": "🇿🇦", "ZA": "🇿🇦",
        "Mexico": "🇲🇽", "MX": "🇲🇽",
        "Argentina": "🇦🇷", "AR": "🇦🇷",
        "Chile": "🇨🇱", "CL": "🇨🇱",
        "Colombia": "🇨🇴", "CO": "🇨🇴",
        "Peru": "🇵🇪", "PE": "🇵🇪",
        "Venezuela": "🇻🇪", "VE": "🇻🇪",
        "Belgium": "🇧🇪", "BE": "🇧🇪",
        "Austria": "🇦🇹", "AT": "🇦🇹",
        "Czech Republic": "🇨🇿", "CZ": "🇨🇿",
        "Denmark": "🇩🇰", "DK": "🇩🇰",
        "Finland": "🇫🇮", "FI": "🇫🇮",
        "Greece": "🇬🇷", "GR": "🇬🇷",
        "Hungary": "🇭🇺", "HU": "🇭🇺",
        "Ireland": "🇮🇪", "IE": "🇮🇪",
        "Norway": "🇳🇴", "NO": "🇳🇴",
        "Portugal": "🇵🇹", "PT": "🇵🇹",
        "Romania": "🇷🇴", "RO": "🇷🇴",
        "Bulgaria": "🇧🇬", "BG": "🇧🇬",
        "Croatia": "🇭🇷", "HR": "🇭🇷",
        "Serbia": "🇷🇸", "RS": "🇷🇸",
        "Slovakia": "🇸🇰", "SK": "🇸🇰",
        "Slovenia": "🇸🇮", "SI": "🇸🇮",
        "Kazakhstan": "🇰🇿", "KZ": "🇰🇿",
        "Belarus": "🇧🇾", "BY": "🇧🇾",
        "Unknown": "🌐"
    }
    return flags.get(country, "🌐")

def create_readme(configs_by_country: dict[str, list[str]], total_configs: int) -> str:
    """Создает красивый README с статистикой по странам."""
    tz = get_timezone()
    if tz:
        date_str = datetime.now(tz).strftime('%d.%m.%Y %H:%M:%S')
    else:
        date_str = datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')
    
    # Сортируем страны по количеству конфигов
    sorted_countries = sorted(
        configs_by_country.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    
    # Формируем статистику по странам с ссылками
    country_stats = []
    for country, configs in sorted_countries:
        flag = get_country_flag_emoji(country)
        count = len(configs)
        percentage = (count * 100) // total_configs if total_configs > 0 else 0
        safe_country = country.replace(" ", "-").replace("/", "-")
        filename = f"subscription-{safe_country}.txt"
        subscription_url = f"https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/{filename}"
        country_stats.append(f"| {flag} {country} | {count} | {percentage}% | [📥 Подписка]({subscription_url}) |")
    
    country_stats_text = "\n".join(country_stats)
    
    # Формируем ссылки на подписки по странам
    subscription_links = []
    for country, configs in sorted_countries:
        flag = get_country_flag_emoji(country)
        # Создаем безопасное имя файла (убираем пробелы и спецсимволы)
        safe_country = country.replace(" ", "-").replace("/", "-")
        filename = f"subscription-{safe_country}.txt"
        subscription_links.append(
            f"- {flag} **{country}** ({len(configs)} конфигов): "
            f"`https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/{filename}`"
        )
    
    subscription_links_text = "\n".join(subscription_links)
    
    readme_content = f"""# 🚀 Hysteria2 Configs Subscription

<div align="center">

<img src="https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/Untitled_without_bg.png" alt="Logo" width="200" style="margin-bottom: 20px;">

### 🌍 Автоматически обновляемая подписка с Hysteria2 конфигами

[![Auto Update](https://img.shields.io/badge/Auto-Update-brightgreen)](https://github.com/{GITHUB_REPO_NAME}/actions)
[![Total Configs](https://img.shields.io/badge/Total-{total_configs}-blue)](./subscription.txt)
[![Last Update](https://img.shields.io/badge/Last_Update-{date_str.replace(' ', '_')}-orange)](./subscription.txt)

</div>

---

## 📊 Статистика последнего обновления

- **📅 Дата обновления:** `{date_str}`
- **📦 Всего конфигов:** `{total_configs}`
- **🌍 Стран:** `{len(configs_by_country)}`

## 📈 Распределение по странам

| Страна | Конфигов | Процент | Подписка |
|--------|----------|---------|----------|
{country_stats_text}

---

## 🔗 Ссылки на подписки

### 📥 Все конфиги

```
https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/subscription.txt
```

### 🌍 Подписки по странам

{subscription_links_text}

---

## 📥 Как использовать

### Hysteria2 клиент

1. Откройте настройки клиента
2. Добавьте подписку (выберите нужную ссылку выше)
3. Конфиги будут автоматически обновляться

### V2RayN / Nekoray / Clash

1. Скопируйте ссылку на подписку
2. Вставьте в настройках подписок
3. Обновите подписку

---

## ⚡ Быстрый старт

1. Выберите подписку из списка выше (все конфиги или по стране)
2. Скопируйте ссылку
3. Добавьте в ваш клиент Hysteria2
4. Готово! 🎉

---

## 👤 Автор

<div align="center">

### 🕐 616 минут

[![Telegram](https://img.shields.io/badge/Telegram-616%20минут-0088cc?style=for-the-badge&logo=telegram)](https://t.me/solnechniyre6enok)

**📢 [Telegram канал](https://t.me/solnechniyre6enok)**

</div>

---

<div align="center">

**⭐ Если проект полезен, поставьте звезду!**

*Последнее обновление: {date_str}*

</div>
"""
    
    return readme_content

def upload_to_github(file_path: str, remote_path: str, content: str = None, is_binary: bool = False):
    """Загружает файл в GitHub репозиторий."""
    if not GITHUB_AVAILABLE:
        log("⚠️ PyGithub не установлен. Установите: pip install PyGithub")
        return False
    
    if not GITHUB_TOKEN or not GITHUB_REPO_NAME:
        log("⚠️ GitHub токен или имя репозитория не заданы. Используйте переменные окружения GITHUB_TOKEN и GITHUB_REPO_NAME")
        return False
    
    try:
        g = Github(auth=Auth.Token(GITHUB_TOKEN))
        repo = g.get_repo(GITHUB_REPO_NAME)
        
        # Определяем, является ли файл бинарным
        if not is_binary and content is None:
            # Проверяем по расширению
            binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.pdf', '.zip', '.exe', '.dll', '.so', '.dylib'}
            file_ext = os.path.splitext(file_path)[1].lower()
            is_binary = file_ext in binary_extensions
        
        # Читаем содержимое файла если не передано
        if content is None:
            if is_binary:
                # Читаем бинарный файл и кодируем в base64
                with open(file_path, "rb") as f:
                    binary_content = f.read()
                    content = base64.b64encode(binary_content).decode('utf-8')
            else:
                # Читаем текстовый файл
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
        
        # Пытаемся получить существующий файл
        try:
            file_in_repo = repo.get_contents(remote_path, ref=GITHUB_BRANCH)
            # Обновляем файл
            tz = get_timezone()
            if tz:
                now = datetime.now(tz)
            else:
                now = datetime.utcnow()
            timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
            
            repo.update_file(
                path=remote_path,
                message=f"🔄 Автоматическое обновление: {timestamp}",
                content=content,
                sha=file_in_repo.sha,
                branch=GITHUB_BRANCH
            )
            log(f"✅ Обновлен файл {remote_path} в GitHub")
        except Exception:
            # Файл не существует, создаем новый
            tz = get_timezone()
            if tz:
                now = datetime.now(tz)
            else:
                now = datetime.utcnow()
            timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
            
            repo.create_file(
                path=remote_path,
                message=f"🆕 Создан файл: {timestamp}",
                content=content,
                branch=GITHUB_BRANCH
            )
            log(f"✅ Создан файл {remote_path} в GitHub")
        
        return True
    except Exception as e:
        log(f"❌ Ошибка при загрузке в GitHub: {str(e)[:200]}")
        return False

# -------------------- ОСНОВНАЯ ФУНКЦИЯ --------------------
def main():
    log("🚀 Начало работы Hysteria2 Checker")
    
    # Создаем директорию для результатов
    if not os.path.exists("results"):
        os.mkdir("results")
    
    # Загружаем конфиги из всех источников
    log(f"📥 Загрузка конфигов из {len(ALL_URLS)} источников...")
    all_configs = []
    
    def download_and_extract(url):
        try:
            data = fetch_data(url)
            if not data:
                return []
            configs = extract_hysteria2_configs(data)
            if configs:
                log(f"✅ {url.split('/')[-1]}: найдено {len(configs)} Hysteria2 конфигов")
            return configs
        except Exception as e:
            log(f"⚠️ Ошибка при обработке {url.split('/')[-1]}: {str(e)[:100]}")
            return []
    
    # Используем более консервативное количество воркеров
    max_workers = min(DEFAULT_MAX_WORKERS, len(ALL_URLS), 30)
    log(f"📥 Используется {max_workers} параллельных потоков")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_and_extract, url): url for url in ALL_URLS}
        
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            try:
                configs = future.result(timeout=30)  # Таймаут на результат
                all_configs.extend(configs)
            except concurrent.futures.TimeoutError:
                log(f"⏱️ Таймаут при обработке {futures[future].split('/')[-1]}")
            except Exception as e:
                log(f"⚠️ Ошибка при получении результата: {str(e)[:100]}")
            
            # Показываем прогресс каждые 10 URL
            if completed % 10 == 0:
                log(f"📊 Прогресс: {completed}/{len(ALL_URLS)} источников обработано, найдено {len(all_configs)} конфигов")
    
    # Умная дедупликация
    log(f"🔍 Найдено конфигов до дедупликации: {len(all_configs)}")
    unique_configs = deduplicate_configs(all_configs, show_log=True)
    removed = len(all_configs) - len(unique_configs)
    if removed > 0:
        log(f"📊 После дедупликации: {len(unique_configs)} уникальных конфигов (удалено {removed} дубликатов)")
    else:
        log(f"📊 Всего найдено уникальных Hysteria2 конфигов: {len(unique_configs)}")
    
    if not unique_configs:
        log("⚠️ Конфигов не найдено!")
        log("✨ Работа завершена!")
        return
    
    # Сортируем конфиги по хосту для удобства
    def get_sort_key(config):
        try:
            parsed = parse_hysteria2_url(config)
            if parsed:
                return (parsed['host'].lower(), parsed['port'])
            return (config.lower(), 0)
        except:
            return (config.lower(), 0)
    
    unique_configs.sort(key=get_sort_key)
    log(f"✅ Всего уникальных Hysteria2 конфигов: {len(unique_configs)}")
    
    # Определяем страны для всех конфигов
    configs_by_country = get_countries_for_configs(unique_configs)
    
    # Создаем основной файл подписки со всеми конфигами
    subscription_file = create_subscription_file(unique_configs, "subscription.txt")
    
    # Загружаем в GitHub если настроено
    if GITHUB_TOKEN and GITHUB_REPO_NAME:
        log("📤 Загрузка файлов в GitHub...")
        
        # Загружаем основной файл подписки
        with open(subscription_file, "r", encoding="utf-8") as f:
            subscription_content = f.read()
        
        upload_to_github(subscription_file, "subscription.txt", subscription_content)
        
        # Создаем файлы подписок по странам
        log(f"🌍 Создание подписок по странам ({len(configs_by_country)} стран)...")
        for country, configs in configs_by_country.items():
            # Создаем безопасное имя файла
            safe_country = country.replace(" ", "-").replace("/", "-")
            country_filename = f"subscription-{safe_country}.txt"
            
            # Создаем файл подписки для страны
            create_subscription_file(configs, country_filename)
            
            # Загружаем в GitHub
            with open(country_filename, "r", encoding="utf-8") as f:
                country_content = f.read()
            
            upload_to_github(country_filename, country_filename, country_content)
            log(f"  ✅ {country}: {len(configs)} конфигов → {country_filename}")
        
        # Загружаем логотип один раз, если его еще нет в репозитории
        logo_path = "Untitled_without_bg.png"
        if os.path.exists(logo_path) and GITHUB_AVAILABLE:
            try:
                g = Github(auth=Auth.Token(GITHUB_TOKEN))
                repo = g.get_repo(GITHUB_REPO_NAME)
                # Проверяем, существует ли файл в репозитории
                try:
                    repo.get_contents(logo_path, ref=GITHUB_BRANCH)
                    # Файл уже существует, не загружаем
                except Exception:
                    # Файла нет, загружаем один раз
                    log("🖼️ Загрузка логотипа в GitHub (первый раз)...")
                    upload_to_github(logo_path, logo_path, is_binary=True)
            except Exception as e:
                log(f"⚠️ Не удалось проверить/загрузить логотип: {str(e)[:100]}")
        
        # Создаем красивый README
        readme_content = create_readme(configs_by_country, len(unique_configs))
        upload_to_github("README.md", "README.md", readme_content)
        
        # Формируем URL подписки
        subscription_url = f"https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/subscription.txt"
        log(f"🔗 URL основной подписки: {subscription_url}")
        log(f"🌍 Создано {len(configs_by_country)} подписок по странам")
    else:
        log("ℹ️ GitHub не настроен. Для автоматической загрузки установите переменные окружения:")
        log("   GITHUB_TOKEN=your_token")
        log("   GITHUB_REPO_NAME=username/repo-name")
    
    log("✨ Работа завершена!")

if __name__ == "__main__":
    main()


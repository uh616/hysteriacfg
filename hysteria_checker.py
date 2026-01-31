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

DEFAULT_MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "50"))  # Увеличено для быстрой проверки
TIMEOUT = 10
PING_TIMEOUT = 3  # Уменьшено для быстрой проверки недоступных серверов
SPEED_TEST_DURATION = 3  # Уменьшено для быстрой проверки скорости

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
def fetch_data(url: str, timeout: int = TIMEOUT, max_attempts: int = 3) -> str:
    """Загружает данные по URL с повторными попытками."""
    for attempt in range(1, max_attempts + 1):
        try:
            modified_url = url
            verify = True

            if attempt == 2:
                verify = False
            elif attempt == 3:
                parsed = urllib.parse.urlparse(url)
                if parsed.scheme == "https":
                    modified_url = parsed._replace(scheme="http").geturl()
                verify = False

            response = REQUESTS_SESSION.get(modified_url, timeout=timeout, verify=verify)
            response.raise_for_status()
            return response.text

        except requests.exceptions.RequestException as exc:
            if attempt < max_attempts:
                continue
            log(f"⚠️ Ошибка при загрузке {url}: {str(exc)[:100]}")
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
def get_country_by_ip(host: str) -> str:
    """Определяет страну по IP адресу."""
    try:
        # Пытаемся получить IP из хоста
        try:
            ip = socket.gethostbyname(host)
        except:
            # Если это уже IP
            if not re.match(r'^\d+\.\d+\.\d+\.\d+$', host):
                return "Unknown"
            ip = host
        
        # Используем бесплатный API для определения страны
        try:
            response = REQUESTS_SESSION.get(
                f"http://ip-api.com/json/{ip}?fields=country",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('country', 'Unknown')
        except:
            pass
        
        return "Unknown"
    except Exception as e:
        return "Unknown"

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

# -------------------- ПРОВЕРКА КОНФИГА --------------------
def check_config(config_url: str) -> dict:
    """Проверяет один конфиг на работоспособность."""
    parsed = parse_hysteria2_url(config_url)
    if not parsed:
        return None
    
    host = parsed['host']
    port = parsed['port']
    
    # Проверяем ping
    ping = check_ping(host, port)
    if ping is None:
        return None  # Сервер недоступен
    
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

# -------------------- GITHUB ФУНКЦИИ --------------------
def create_subscription_file(working_configs: list) -> str:
    """Создает файл подписки с рабочими конфигами."""
    # Дедупликация рабочих конфигов перед созданием файла
    config_urls = [cfg['config'] for cfg in working_configs]
    unique_config_urls = deduplicate_configs(config_urls, show_log=False)
    
    subscription_content = "\n".join(unique_config_urls)
    
    # Сохраняем локально
    subscription_file = "subscription.txt"
    with open(subscription_file, "w", encoding="utf-8") as f:
        f.write(subscription_content)
    
    removed = len(working_configs) - len(unique_config_urls)
    if removed > 0:
        log(f"🔍 Удалено {removed} дубликатов из рабочих конфигов перед созданием подписки")
    log(f"📝 Создан файл подписки: {subscription_file} ({len(unique_config_urls)} уникальных конфигов)")
    return subscription_file

def upload_to_github(file_path: str, remote_path: str, content: str = None):
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
        
        # Читаем содержимое файла если не передано
        if content is None:
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
                message=f"🆕 Создан файл подписки: {timestamp}",
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
                log(f"⚠️ Пустой ответ от {url}")
                return []
            configs = extract_hysteria2_configs(data)
            if configs:
                log(f"✅ {url.split('/')[-1]}: найдено {len(configs)} Hysteria2 конфигов")
            return configs
        except Exception as e:
            log(f"⚠️ Ошибка при обработке {url.split('/')[-1]}: {str(e)[:100]}")
            return []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(DEFAULT_MAX_WORKERS, len(ALL_URLS))) as executor:
        futures = [executor.submit(download_and_extract, url) for url in ALL_URLS]
        for future in concurrent.futures.as_completed(futures):
            configs = future.result()
            all_configs.extend(configs)
    
    # Умная дедупликация
    log(f"🔍 Найдено конфигов до дедупликации: {len(all_configs)}")
    unique_configs = deduplicate_configs(all_configs, show_log=True)
    removed = len(all_configs) - len(unique_configs)
    if removed > 0:
        log(f"📊 После дедупликации: {len(unique_configs)} уникальных конфигов (удалено {removed} дубликатов)")
    else:
        log(f"📊 Всего найдено уникальных Hysteria2 конфигов: {len(unique_configs)}")
    
    # Проверяем конфиги
    log(f"🔍 Начинаем проверку {len(unique_configs)} конфигов...")
    working_configs = []
    checked_count = 0
    failed_count = 0
    
    def check_one_config(config):
        nonlocal checked_count, failed_count
        try:
            result = check_config(config)
            checked_count += 1
            if result:
                working_configs.append(result)
                log(f"✅ [{checked_count}/{len(unique_configs)}] Рабочий: {result['host']}:{result['port']} ({result['country']}) - Ping: {result['ping']}ms - Speed: {result['speed']}")
            else:
                failed_count += 1
                # Показываем прогресс каждые 50 проверок для ускорения вывода
                if checked_count % 50 == 0:
                    progress_pct = (checked_count / len(unique_configs)) * 100
                    log(f"📊 Прогресс: {checked_count}/{len(unique_configs)} ({progress_pct:.1f}%) | Рабочих: {len(working_configs)} | Недоступных: {failed_count}")
            return result
        except Exception as e:
            checked_count += 1
            failed_count += 1
            return None
    
    # Увеличиваем количество потоков для проверки
    max_check_workers = min(DEFAULT_MAX_WORKERS, 100)
    log(f"⚙️ Используется {max_check_workers} параллельных потоков для проверки")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_check_workers) as executor:
        futures = [executor.submit(check_one_config, config) for config in unique_configs]
        for future in concurrent.futures.as_completed(futures):
            _ = future.result()
    
    # Статистика
    success_rate = (len(working_configs) / len(unique_configs) * 100) if unique_configs else 0
    log(f"✅ Найдено рабочих конфигов: {len(working_configs)} из {len(unique_configs)} ({success_rate:.1f}%)")
    
    if not working_configs:
        log("⚠️ Рабочих конфигов не найдено!")
        log("✨ Работа завершена!")
        return
    
    # Сортируем по ping
    working_configs.sort(key=lambda x: x['ping'])
    
    # Статистика по странам
    countries = {}
    for config in working_configs:
        country = config['country']
        countries[country] = countries.get(country, 0) + 1
    
    # Статистика по скорости
    speeds = {}
    for config in working_configs:
        speed = config['speed']
        speeds[speed] = speeds.get(speed, 0) + 1
    
    # Сохраняем результаты
    tz = get_timezone()
    if tz:
        timestamp = datetime.now(tz).strftime("%Y%m%d_%H%M%S")
        date_str = datetime.now(tz).strftime('%d.%m.%Y %H:%M:%S')
    else:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        date_str = datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')
    output_file = f"results/hysteria2_results_{timestamp}.txt"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("HYSTERIA2 CONFIG CHECKER - РЕЗУЛЬТАТЫ ПРОВЕРКИ\n")
        f.write("=" * 80 + "\n")
        f.write(f"Дата проверки: {date_str}\n")
        f.write(f"Всего проверено: {len(unique_configs)}\n")
        f.write(f"Рабочих конфигов: {len(working_configs)} ({success_rate:.1f}%)\n")
        f.write(f"Недоступных: {failed_count}\n")
        f.write("\n")
        
        # Статистика по странам
        if countries:
            f.write("СТАТИСТИКА ПО СТРАНАМ:\n")
            f.write("-" * 80 + "\n")
            for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {country}: {count} конфигов\n")
            f.write("\n")
        
        # Статистика по скорости
        if speeds:
            f.write("СТАТИСТИКА ПО СКОРОСТИ:\n")
            f.write("-" * 80 + "\n")
            for speed, count in sorted(speeds.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {speed}: {count} конфигов\n")
            f.write("\n")
        
        f.write("=" * 80 + "\n")
        f.write("ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ (отсортированы по ping):\n")
        f.write("=" * 80 + "\n\n")
        
        for i, config_info in enumerate(working_configs, 1):
            f.write(f"{i}. Конфиг: {config_info['config']}\n")
            f.write(f"   Хост: {config_info['host']}:{config_info['port']}\n")
            f.write(f"   Страна: {config_info['country']}\n")
            f.write(f"   Ping: {config_info['ping']} ms\n")
            f.write(f"   Скорость: {config_info['speed']}\n")
            if config_info.get('connection_time'):
                f.write(f"   Время соединения: {config_info['connection_time']} сек\n")
            if config_info.get('transfer_time'):
                f.write(f"   Время передачи: {config_info['transfer_time']} сек\n")
            if config_info.get('total_time'):
                f.write(f"   Общее время: {config_info['total_time']} сек\n")
            f.write("\n")
    
    log(f"💾 Результаты сохранены в {output_file}")
    log(f"📊 Статистика: {len(countries)} стран, {len(speeds)} категорий скорости")
    
    # Создаем файл подписки
    subscription_file = create_subscription_file(working_configs)
    
    # Загружаем в GitHub если настроено
    if GITHUB_TOKEN and GITHUB_REPO_NAME:
        log("📤 Загрузка файлов в GitHub...")
        
        # Загружаем файл подписки
        with open(subscription_file, "r", encoding="utf-8") as f:
            subscription_content = f.read()
        
        upload_to_github(subscription_file, "subscription.txt", subscription_content)
        
        # Создаем README с информацией о подписке
        readme_content = f"""# Hysteria2 Working Configs

Автоматически обновляемая подписка с проверенными рабочими Hysteria2 конфигами.

## 📊 Статистика последнего обновления

- **Дата обновления:** {date_str}
- **Всего проверено:** {len(unique_configs)} конфигов
- **Рабочих конфигов:** {len(working_configs)} ({success_rate:.1f}%)
- **Стран:** {len(countries)}
- **Категорий скорости:** {len(speeds)}

## 🔗 Ссылка на подписку

Используйте эту ссылку для автоматического обновления конфигов:

```
https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/subscription.txt
```

## 📥 Как использовать

### Hysteria2 клиент
1. Откройте настройки клиента
2. Добавьте подписку: `https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/subscription.txt`
3. Конфиги будут автоматически обновляться

### Вручную
Скачайте файл `subscription.txt` и импортируйте конфиги в ваш клиент.

## 📈 Статистика по странам

"""
        for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
            readme_content += f"- {country}: {count} конфигов\n"
        
        readme_content += "\n## ⚡ Статистика по скорости\n\n"
        for speed, count in sorted(speeds.items(), key=lambda x: x[1], reverse=True):
            readme_content += f"- {speed}: {count} конфигов\n"
        
        readme_content += f"""

## 🔄 Автоматическое обновление

Этот репозиторий автоматически обновляется каждый час с проверенными рабочими конфигами.

---
*Последнее обновление: {date_str}*
"""
        
        upload_to_github("README.md", "README.md", readme_content)
        
        # Формируем URL подписки
        subscription_url = f"https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/subscription.txt"
        log(f"🔗 URL подписки: {subscription_url}")
    else:
        log("ℹ️ GitHub не настроен. Для автоматической загрузки установите переменные окружения:")
        log("   GITHUB_TOKEN=your_token")
        log("   GITHUB_REPO_NAME=username/repo-name")
    
    log("✨ Работа завершена!")

if __name__ == "__main__":
    main()


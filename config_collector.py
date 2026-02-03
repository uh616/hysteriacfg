"""
Multi-Protocol Config Collector
Скрипт для сбора и организации конфигов различных протоколов (Hysteria2, VLESS, VMESS, Shadowsocks, Trojan)
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

# QR Code (опционально)
QRCODE_AVAILABLE = False
try:
    import qrcode
    from PIL import Image
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

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

def extract_vless_configs(data: str) -> list[str]:
    """Извлекает все VLESS конфиги из текста."""
    configs = []
    data = re.sub(r'<[^>]+>', '', data)
    patterns = [
        r'vless://[^\s\n<>"\'\)]+',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, data, re.IGNORECASE)
        configs.extend(matches)
    # Base64 декодирование
    try:
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
    cleaned_configs = []
    for cfg in configs:
        cfg = cfg.rstrip('.,;:!?)\'"')
        if len(cfg) > 10 and ('://' in cfg):
            cleaned_configs.append(cfg)
    return list(dict.fromkeys(cleaned_configs))

def extract_vmess_configs(data: str) -> list[str]:
    """Извлекает все VMESS конфиги из текста."""
    configs = []
    data = re.sub(r'<[^>]+>', '', data)
    patterns = [
        r'vmess://[^\s\n<>"\'\)]+',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, data, re.IGNORECASE)
        configs.extend(matches)
    # Base64 декодирование
    try:
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
    cleaned_configs = []
    for cfg in configs:
        cfg = cfg.rstrip('.,;:!?)\'"')
        if len(cfg) > 10 and ('://' in cfg):
            cleaned_configs.append(cfg)
    return list(dict.fromkeys(cleaned_configs))

def extract_shadowsocks_configs(data: str) -> list[str]:
    """Извлекает все Shadowsocks конфиги из текста."""
    configs = []
    data = re.sub(r'<[^>]+>', '', data)
    patterns = [
        r'ss://[^\s\n<>"\'\)]+',
        r'shadowsocks://[^\s\n<>"\'\)]+',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, data, re.IGNORECASE)
        configs.extend(matches)
    # Base64 декодирование
    try:
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
    cleaned_configs = []
    for cfg in configs:
        cfg = cfg.rstrip('.,;:!?)\'"')
        if len(cfg) > 10 and ('://' in cfg):
            cleaned_configs.append(cfg)
    return list(dict.fromkeys(cleaned_configs))

def extract_trojan_configs(data: str) -> list[str]:
    """Извлекает все Trojan конфиги из текста."""
    configs = []
    data = re.sub(r'<[^>]+>', '', data)
    patterns = [
        r'trojan://[^\s\n<>"\'\)]+',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, data, re.IGNORECASE)
        configs.extend(matches)
    # Base64 декодирование
    try:
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
    cleaned_configs = []
    for cfg in configs:
        cfg = cfg.rstrip('.,;:!?)\'"')
        if len(cfg) > 10 and ('://' in cfg):
            cleaned_configs.append(cfg)
    return list(dict.fromkeys(cleaned_configs))

def normalize_config_url(config_url: str) -> str:
    """Нормализует URL конфига для сравнения (универсальная для всех протоколов)."""
    try:
        # Для других протоколов просто возвращаем как есть (можно улучшить позже)
        if not config_url.startswith(('hysteria2://', 'hy2://', 'vless://', 'vmess://', 'ss://', 'shadowsocks://', 'trojan://')):
            return config_url
        
        # Hysteria2 - полная нормализация
        if config_url.startswith(('hysteria2://', 'hy2://')):
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

def deduplicate_configs(configs: list[str], protocol: str = None, show_log: bool = True) -> list[str]:
    """Умная дедупликация конфигов по host:port и полному URL с учетом протокола."""
    seen_full = set()  # Полные нормализованные URL
    seen_hostport = set()  # host:port для проверки дубликатов (с учетом протокола)
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
        
        # Определяем протокол из конфига, если не передан
        config_protocol = protocol
        if not config_protocol:
            if config.startswith(('hysteria2://', 'hy2://')):
                config_protocol = 'hysteria2'
            elif config.startswith('vless://'):
                config_protocol = 'vless'
            elif config.startswith('vmess://'):
                config_protocol = 'vmess'
            elif config.startswith('ss://'):
                config_protocol = 'shadowsocks'
            elif config.startswith('trojan://'):
                config_protocol = 'trojan'
            else:
                config_protocol = 'unknown'
        
        # Парсим для проверки host:port (универсально для всех протоколов)
        host_port = extract_host_from_config(config)
        if host_port:
            host, port = host_port
            host = host.lower().strip()
            # Включаем протокол в ключ, чтобы разные протоколы с одинаковым host:port не считались дубликатами
            hostport_key = f"{config_protocol}:{host}:{port}"
            
            # Проверяем дубликат по host:port (только для того же протокола)
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

def extract_host_from_config(config_url: str) -> tuple[str, int] | None:
    """Универсальная функция для извлечения хоста и порта из любого типа конфига."""
    try:
        # Hysteria2
        if config_url.startswith(('hysteria2://', 'hy2://')):
            parsed = parse_hysteria2_url(config_url)
            if parsed:
                return (parsed['host'], parsed['port'])
        
        # VLESS, VMESS, Trojan - формат protocol://uuid@host:port?params
        elif config_url.startswith(('vless://', 'vmess://', 'trojan://')):
            url_part = config_url.split('://', 1)[1]
            if '#' in url_part:
                url_part = url_part.split('#')[0]
            if '@' in url_part:
                _, rest = url_part.rsplit('@', 1)
                if '?' in rest:
                    host_port = rest.split('?')[0]
                else:
                    host_port = rest
                if '[' in host_port and ']' in host_port:
                    match = re.match(r'\[([^\]]+)\]:(\d+)', host_port)
                    if match:
                        return (match.group(1), int(match.group(2)))
                elif ':' in host_port:
                    parts = host_port.rsplit(':', 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        return (parts[0], int(parts[1]))
        
        # Shadowsocks - формат ss://base64@host:port или ss://method:password@host:port
        elif config_url.startswith('ss://'):
            url_part = config_url.split('://', 1)[1]
            if '#' in url_part:
                url_part = url_part.split('#')[0]
            if '@' in url_part:
                _, rest = url_part.rsplit('@', 1)
                if '[' in rest and ']' in rest:
                    match = re.match(r'\[([^\]]+)\]:(\d+)', rest)
                    if match:
                        return (match.group(1), int(match.group(2)))
                elif ':' in rest:
                    parts = rest.rsplit(':', 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        return (parts[0], int(parts[1]))
        
        return None
    except:
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
    """Определяет страны для всех конфигов и группирует их (универсальная для всех протоколов)."""
    configs_by_country = {}
    total = len(configs)
    processed = 0
    
    def process_config(config):
        nonlocal processed
        try:
            host_port = extract_host_from_config(config)
            if not host_port:
                processed += 1
                return None, "Unknown"
            
            host, _ = host_port
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

# -------------------- QR CODE ФУНКЦИИ --------------------
def generate_qr_code(config_url: str, output_path: str) -> bool:
    """Генерирует QR-код для конфига."""
    if not QRCODE_AVAILABLE:
        return False
    
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(config_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_path)
        return True
    except Exception:
        return False

def generate_qr_for_subscription_url(subscription_url: str, output_path: str) -> bool:
    """Генерирует QR-код для ссылки на подписку."""
    if not QRCODE_AVAILABLE:
        return False
    return generate_qr_code(subscription_url, output_path)

# -------------------- НУМЕРОВАННЫЕ ПОДПИСКИ --------------------
def create_numbered_subscriptions(configs: list[str], protocol_folder: str, max_subscriptions: int = 10) -> list[str]:
    """Создает нумерованные подписки (best-1.txt, best-2.txt и т.д.) с лучшими конфигами."""
    if not configs:
        return []
    
    # Разделяем конфиги на группы примерно равного размера
    configs_per_sub = max(1, len(configs) // max_subscriptions)
    subscriptions = []
    
    for i in range(max_subscriptions):
        start_idx = i * configs_per_sub
        end_idx = start_idx + configs_per_sub if i < max_subscriptions - 1 else len(configs)
        
        if start_idx >= len(configs):
            break
        
        subset = configs[start_idx:end_idx]
        if not subset:
            continue
        
        filename = f"{protocol_folder}/best-{i+1}.txt"
        create_subscription_file(subset, filename)
        subscriptions.append(filename)
    
    return subscriptions

# -------------------- GITHUB ФУНКЦИИ --------------------
def create_subscription_file(configs: list[str], filename: str = "subscription.txt") -> str:
    """Создает файл подписки со всеми конфигами."""
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
    
    readme_content = f"""# ⚡ REBORN CFG

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

def create_readme_multi_protocol(protocol_stats: dict) -> str:
    """Создает красивый README с информацией о всех протоколах."""
    tz = get_timezone()
    if tz:
        date_str = datetime.now(tz).strftime('%d.%m.%Y %H:%M:%S')
    else:
        date_str = datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')
    
    # Названия протоколов с эмодзи
    protocol_names = {
        'hysteria2': '🚀 Hysteria2',
        'vless': '⚡ VLESS',
        'vmess': '🔷 VMESS',
        'shadowsocks': '🔰 Shadowsocks',
        'trojan': '🎯 Trojan'
    }
    
    total_configs = sum(s['total'] for s in protocol_stats.values())
    total_countries = set()
    for stats in protocol_stats.values():
        total_countries.update(stats['by_country'].keys())
    
    # Формируем секции для каждого протокола
    protocol_sections = []
    
    for protocol, stats in protocol_stats.items():
        protocol_name = protocol_names.get(protocol, protocol.upper())
        protocol_folder = protocol
        total = stats['total']
        configs_by_country = stats['by_country']
        
        # Сортируем страны по количеству конфигов
        sorted_countries = sorted(
            configs_by_country.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        # Таблица по странам (топ 10)
        country_table = []
        for country, configs in sorted_countries[:10]:  # Топ 10 стран
            flag = get_country_flag_emoji(country)
            count = len(configs)
            percentage = (count * 100) // total if total > 0 else 0
            safe_country = country.replace(" ", "-").replace("/", "-")
            subscription_url = f"https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/{protocol_folder}/subscription-{safe_country}.txt"
            country_table.append(f"| {flag} {country} | {count} | {percentage}% | [📥]({subscription_url}) |")
        
        country_table_text = "\n".join(country_table) if country_table else "| - | - | - | - |"
        
        # Полный список стран для спойлера (более компактный формат)
        all_countries_list = []
        for country, configs in sorted_countries:
            flag = get_country_flag_emoji(country)
            count = len(configs)
            safe_country = country.replace(" ", "-").replace("/", "-")
            subscription_url = f"https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/{protocol_folder}/subscription-{safe_country}.txt"
            all_countries_list.append(f"{flag} **{country}** ({count}): [`{subscription_url}`]({subscription_url})")
        
        all_countries_text = "\n".join(all_countries_list) if all_countries_list else "- Нет конфигов"
        
        # Основная ссылка на подписку
        main_subscription = f"https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/{protocol_folder}/subscription.txt"
        
        # QR код для основной подписки - используем прямой URL (надежнее чем base64)
        qr_filename = f"{protocol_folder}/subscription-qr.png"
        qr_url = f"https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/{qr_filename}"
        # Используем прямой URL, так как файл уже загружен в GitHub
        qr_image_html = f'<img src="{qr_url}" alt="QR Code" width="200" style="display: block; margin: 0 auto;">'
        
        # Рекомендуемые нумерованные подписки (best-1, best-2, best-3)
        recommended_subs = []
        for i in [1, 2, 3]:
            best_sub = f"https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/{protocol_folder}/best-{i}.txt"
            recommended_subs.append(f"`{best_sub}`")
        
        recommended_text = "\n".join([f"{i+1}. {sub}" for i, sub in enumerate(recommended_subs)])
        
        protocol_section = f"""
### {protocol_name}

**📦 Всего конфигов:** `{total}` | **🌍 Стран:** `{len(configs_by_country)}`

**📥 Основная подписка:**
```
{main_subscription}
```

**📱 QR-код подписки:**

{qr_image_html}

**⭐ Рекомендуемые подписки:**
{recommended_text}

**📊 Топ стран:**

| Страна | Конфигов | Процент | Подписка |
|--------|----------|---------|----------|
{country_table_text}

<details>
<summary>🌍 Все страны ({len(sorted_countries)} стран) - нажмите чтобы развернуть</summary>

{all_countries_text}

</details>

"""
        protocol_sections.append(protocol_section)
    
    protocol_sections_text = "\n".join(protocol_sections)
    
    readme_content = f"""# ⚡ REBORN CFG

<div align="center">

<img src="https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/Untitled_without_bg.png" alt="Logo" width="200" style="margin-bottom: 20px;">

### ɪ ᴅɪᴇᴅ ꜱɪx ʜᴜɴᴅʀᴇᴅ ᴀɴᴅ ꜱɪxᴛᴇᴇɴ ᴍɪɴᴜᴛᴇꜱ ᴀɢᴏ.

[![Auto Update](https://img.shields.io/badge/Auto-Update-brightgreen)](https://github.com/{GITHUB_REPO_NAME}/actions)
[![Total Configs](https://img.shields.io/badge/Total-{total_configs}-blue)](./hysteria2/subscription.txt)
[![Last Update](https://img.shields.io/badge/Last_Update-{date_str.replace(' ', '_')}-orange)](./hysteria2/subscription.txt)

</div>

---

## 📊 Статистика последнего обновления

- **📅 Дата обновления:** `{date_str}`
- **📦 Всего конфигов:** `{total_configs}`
- **🌍 Всего стран:** `{len(total_countries)}`
- **🔌 Протоколов:** `{len(protocol_stats)}`

---

## 🔌 Подписки по протоколам

{protocol_sections_text}

---

## 📥 Как использовать

### V2RayN / Nekoray / Clash / Hysteria2 клиент

1. Выберите нужный протокол выше
2. Скопируйте ссылку на подписку (все конфиги или по стране)
3. Добавьте в настройках подписок вашего клиента
4. Обновите подписку
5. Готово! 🎉

---

## 👤 Автор

<div align="center">

### 🕐 616 минут

[![Telegram](https://img.shields.io/badge/Telegram-616%20минут-0088cc?style=for-the-badge&logo=telegram)](https://t.me/solnechniyre6enok)

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
        except Exception as e:
            # Файл не существует или ошибка получения SHA, создаем/обновляем
            tz = get_timezone()
            if tz:
                now = datetime.now(tz)
            else:
                now = datetime.utcnow()
            timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
            
            # Пробуем создать файл (если не существует) или обновить (если существует но SHA недоступен)
            try:
                repo.create_file(
                    path=remote_path,
                    message=f"🆕 Создан файл: {timestamp}",
                    content=content,
                    branch=GITHUB_BRANCH
                )
                log(f"✅ Создан файл {remote_path} в GitHub")
            except Exception as create_error:
                # Если файл существует, пробуем получить его снова и обновить
                try:
                    file_in_repo = repo.get_contents(remote_path, ref=GITHUB_BRANCH)
                    repo.update_file(
                        path=remote_path,
                        message=f"🔄 Автоматическое обновление: {timestamp}",
                        content=content,
                        sha=file_in_repo.sha,
                        branch=GITHUB_BRANCH
                    )
                    log(f"✅ Обновлен файл {remote_path} в GitHub (повторная попытка)")
                except Exception as update_error:
                    log(f"⚠️ Не удалось создать/обновить файл {remote_path}: {str(update_error)[:100]}")
                    return False
        
        return True
    except Exception as e:
        log(f"❌ Ошибка при загрузке в GitHub: {str(e)[:200]}")
        return False

# -------------------- ОСНОВНАЯ ФУНКЦИЯ --------------------
def main():
    log("🚀 Начало работы Multi-Protocol Config Collector")
    
    # Создаем директорию для результатов
    if not os.path.exists("results"):
        os.mkdir("results")
    
    # Загружаем конфиги из всех источников
    log(f"📥 Загрузка конфигов из {len(ALL_URLS)} источников...")
    all_configs = []
    
    def download_and_extract(url):
        """Извлекает все типы конфигов из URL."""
        try:
            data = fetch_data(url)
            if not data:
                return {}
            
            result = {
                'hysteria2': extract_hysteria2_configs(data),
                'vless': extract_vless_configs(data),
                'vmess': extract_vmess_configs(data),
                'shadowsocks': extract_shadowsocks_configs(data),
                'trojan': extract_trojan_configs(data),
            }
            
            total = sum(len(v) for v in result.values())
            if total > 0:
                found = [f"{k}:{len(v)}" for k, v in result.items() if len(v) > 0]
                log(f"✅ {url.split('/')[-1]}: найдено {total} конфигов ({', '.join(found)})")
            
            return result
        except Exception as e:
            log(f"⚠️ Ошибка при обработке {url.split('/')[-1]}: {str(e)[:100]}")
            return {}
    
    # Используем более консервативное количество воркеров
    max_workers = min(DEFAULT_MAX_WORKERS, len(ALL_URLS), 30)
    log(f"📥 Используется {max_workers} параллельных потоков")
    
    # Словарь для хранения конфигов по типам протоколов
    configs_by_protocol = {
        'hysteria2': [],
        'vless': [],
        'vmess': [],
        'shadowsocks': [],
        'trojan': []
    }
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_and_extract, url): url for url in ALL_URLS}
        
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            try:
                result = future.result(timeout=30)
                for protocol, configs in result.items():
                    configs_by_protocol[protocol].extend(configs)
            except concurrent.futures.TimeoutError:
                log(f"⏱️ Таймаут при обработке {futures[future].split('/')[-1]}")
            except Exception as e:
                log(f"⚠️ Ошибка при получении результата: {str(e)[:100]}")
            
            # Показываем прогресс каждые 10 URL
            if completed % 10 == 0:
                total = sum(len(v) for v in configs_by_protocol.values())
                log(f"📊 Прогресс: {completed}/{len(ALL_URLS)} источников обработано, найдено {total} конфигов")
    
    # Обрабатываем каждый тип протокола
    protocol_stats = {}
    
    for protocol, configs in configs_by_protocol.items():
        if not configs:
            continue
        
        log(f"\n🔍 Обработка {protocol.upper()} конфигов...")
        log(f"📊 Найдено {len(configs)} конфигов до дедупликации")
        
        # Дедупликация с учетом протокола
        unique_configs = deduplicate_configs(configs, protocol=protocol, show_log=True)
        removed = len(configs) - len(unique_configs)
        if removed > 0:
            log(f"📊 После дедупликации: {len(unique_configs)} уникальных конфигов (удалено {removed} дубликатов)")
        
        if not unique_configs:
            continue
        
        # Сортируем конфиги
        def get_sort_key(config):
            try:
                host_port = extract_host_from_config(config)
                if host_port:
                    return (host_port[0].lower(), host_port[1])
                return (config.lower(), 0)
            except:
                return (config.lower(), 0)
        
        unique_configs.sort(key=get_sort_key)
        
        # Определяем страны
        configs_by_country = get_countries_for_configs(unique_configs)
        
        protocol_stats[protocol] = {
            'total': len(unique_configs),
            'by_country': configs_by_country
        }
        
        log(f"✅ {protocol.upper()}: {len(unique_configs)} уникальных конфигов, {len(configs_by_country)} стран")
    
    if not protocol_stats:
        log("⚠️ Конфигов не найдено!")
        log("✨ Работа завершена!")
        return
    
    # Загружаем в GitHub если настроено
    if GITHUB_TOKEN and GITHUB_REPO_NAME:
        log("\n📤 Загрузка файлов в GitHub...")
        
        # Обрабатываем каждый протокол
        for protocol, stats in protocol_stats.items():
            protocol_folder = protocol
            unique_configs = []
            for country_configs in stats['by_country'].values():
                unique_configs.extend(country_configs)
            
            log(f"\n📁 Обработка {protocol.upper()}...")
            
            # Создаем основной файл подписки для протокола
            subscription_file = f"{protocol_folder}/subscription.txt"
            os.makedirs(protocol_folder, exist_ok=True)
            create_subscription_file(unique_configs, subscription_file)
            
            with open(subscription_file, "r", encoding="utf-8") as f:
                subscription_content = f.read()
            
            upload_to_github(subscription_file, subscription_file, subscription_content)
            
            # Создаем нумерованные подписки (best-1.txt, best-2.txt и т.д.)
            numbered_subs = create_numbered_subscriptions(unique_configs, protocol_folder, max_subscriptions=10)
            for numbered_sub in numbered_subs:
                with open(numbered_sub, "r", encoding="utf-8") as f:
                    numbered_content = f.read()
                upload_to_github(numbered_sub, numbered_sub, numbered_content)
            
            if numbered_subs:
                log(f"  📋 Создано {len(numbered_subs)} нумерованных подписок")
            
            # Генерируем QR-код для основной подписки
            qr_filename = f"{protocol_folder}/subscription-qr.png"
            subscription_url = f"https://raw.githubusercontent.com/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}/{subscription_file}"
            
            if generate_qr_for_subscription_url(subscription_url, qr_filename):
                # Сохраняем файл локально, чтобы он был доступен при создании README
                upload_to_github(qr_filename, qr_filename, is_binary=True)
                log(f"  📱 QR-код для основной подписки создан")
            
            # Создаем файлы подписок по странам
            configs_by_country = stats['by_country']
            if configs_by_country:
                log(f"🌍 Создание подписок по странам для {protocol.upper()} ({len(configs_by_country)} стран)...")
                for country, configs in configs_by_country.items():
                    safe_country = country.replace(" ", "-").replace("/", "-")
                    country_filename = f"{protocol_folder}/subscription-{safe_country}.txt"
                    
                    create_subscription_file(configs, country_filename)
                    
                    with open(country_filename, "r", encoding="utf-8") as f:
                        country_content = f.read()
                    
                    upload_to_github(country_filename, country_filename, country_content)
                    log(f"  ✅ {country}: {len(configs)} конфигов")
        
        # Загружаем логотип один раз, если его еще нет в репозитории
        logo_path = "Untitled_without_bg.png"
        if os.path.exists(logo_path) and GITHUB_AVAILABLE:
            try:
                g = Github(auth=Auth.Token(GITHUB_TOKEN))
                repo = g.get_repo(GITHUB_REPO_NAME)
                try:
                    repo.get_contents(logo_path, ref=GITHUB_BRANCH)
                except Exception:
                    log("🖼️ Загрузка логотипа в GitHub (первый раз)...")
                    upload_to_github(logo_path, logo_path, is_binary=True)
            except Exception as e:
                log(f"⚠️ Не удалось проверить/загрузить логотип: {str(e)[:100]}")
        
        # Создаем красивый README со всеми протоколами (после того как все QR-коды созданы)
        readme_content = create_readme_multi_protocol(protocol_stats)
        upload_to_github("README.md", "README.md", readme_content)
        
        total_configs = sum(s['total'] for s in protocol_stats.values())
        log(f"\n✅ Всего загружено: {total_configs} конфигов по {len(protocol_stats)} протоколам")
    else:
        log("ℹ️ GitHub не настроен. Для автоматической загрузки установите переменные окружения:")
        log("   GITHUB_TOKEN=your_token")
        log("   GITHUB_REPO_NAME=username/repo-name")
    
    log("✨ Работа завершена!")

if __name__ == "__main__":
    main()


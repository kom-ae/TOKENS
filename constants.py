import os
from pathlib import Path

# Директория запуска скрипта
BASE_DIR = Path(__file__).resolve().parent

# Библиотеки для работы с токенами
RT_PKCS11_LIB = r'C:\Windows\System32\rtPKCS11.dll'
JC_PKCS11_LIB = r'C:\Windows\System32\jcPKCS11-2.dll'
LIST_LIBS = [
    RT_PKCS11_LIB,
    JC_PKCS11_LIB,
]

# Настройки токенов
TOKEN_CONF = {
    'Rutoken S': {
        'rtadmin_path': BASE_DIR.joinpath(r'utils\rtadmin\rtAdmin_1.3.exe'),
    },
    'Rutoken lite': {
        'rtadmin_path': BASE_DIR.joinpath(r'utils\rtadmin\rtadmin_3.1.exe'),
    },
    'Rutoken ECP': {
        'rtadmin_path': BASE_DIR.joinpath(r'utils\rtadmin\rtAdmin_3.1.exe'),
    },
    # 'JaCarta Laser': {
    #     'rtadmin_path': None),
    # }
}

# Черный список серийных номеров токенов
BLACK_LIST_TOKENS = [
    '0B53001435596976',
    '4C54000351574C50',
]

# Пин коды администратора
PIN_ADMIN = os.getenv('PIN_ADMIN', '11111111')
PIN_ADMIN_DEFAULT = '87654321'
LIST_PIN_ADMIN = [
    '14444',
    PIN_ADMIN,
    PIN_ADMIN_DEFAULT,
]

# --------------- Политики ПИН кодов ---------------

# Минимальные длины пин кодов
MIN_USER_PIN = 6
MIN_SO_PIN = 6

# Кто может менять пин код пользователя(3 - Администратор и пользователь)
MODE_CHANGE_PIN = 3

# Максимальное количество попыток ввода PIN-кода пользователя
MAX_PIN_COUNT_USER = 10
# Максимальное количество попыток ввода PIN-кода администратора
MAX_PIN_COUNT_SO = 10

# --------------- Параметры токена ---------------

# Максимальная длина имени токена
MAX_LEN_LABEL = 32

# Максимальная длина пин кода
MAX_LEN_PIN = 16

# Пин код пользователя по умолчанию, для форматирования на хранение
DEFAULT_USER_PIN = '12345678'

# --------------- Параметры LDAP ---------------
# Контроллер домена FQDN 
DC_SERVER = os.getenv('LOGONSERVER')[2:]
# Домен
DOMAIN = os.getenv('USERDOMAIN')
# Порт подключения к LDAP
LDAP_PORT = 389  # LDAPS 636
# OU поиска
SEARCH_BASE = os.getenv('LDAP_SEARCH_BASE')
# Таймаут подключения к серверу, сек.
LDAP_CON_TIMEOUT = 10
# Таймаут выполнения запроса
LDAP_SEARCH_TIMEOUT = 30

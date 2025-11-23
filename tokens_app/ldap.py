from typing import List, Dict, Optional
from ldap3 import Server, Connection, SASL, GSSAPI
from ldap3.core.exceptions import LDAPBindError, LDAPSocketOpenError
import winkerberos as kerberos
import logging


from constants import DC_SERVER, DOMAIN, LDAP_PORT, SEARCH_BASE

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_users_from_ou_kerberos(
    server_address: str,
    port: int = 636,
    base_ou: str,
    search_filter: str = '(objectClass=user)',
    attributes: List[str] = None,
    timeout: int = 30,
    connect_timeout: int = 10,
    realm: str = None
) -> List[Dict]:
    """
    Получить пользователей из OU через Kerberos‑аутентификацию.
    
    :param server_address: адрес LDAP‑сервера
    :param port: порт LDAP (обычно 636 для LDAPS)
    :param base_ou: базовая OU для поиска
    :param search_filter: фильтр LDAP
    :param attributes: список атрибутов для извлечения
    :param timeout: таймаут операции (сек)
    :param connect_timeout: таймаут подключения (сек)
    :param realm: Kerberos‑домен (например, 'EXAMPLE.COM')
    :return: список словарей с данными пользователей
    """
    users = []
    try:
        server = Server(
            DC_SERVER,
            port=LDAP_PORT,
            use_ssl=False,
            get_info='NO_INFO',
            connect_timeout=connect_timeout
        )

        # Подготовка GSSAPI-контекста
        # if realm:
        #     principal = gssapi.Name('ldap@' + server_address, gssapi.C_NT_HOSTBASED_SERVICE)
        # else:
        #     principal = gssapi.Name('ldap/' + server_address)

        conn = Connection(
            server,
            authentication=SASL,
            sasl_mechanism=GSSAPI,
            # user=str(principal),
            auto_bind=True,
            read_only=True,
            raise_exceptions=False,

        )

        # Проверяем, кто мы
        print("Аутентифицирован как:", conn.extend.standard.who_am_i())

        conn.search(
            search_base=SEARCH_BASE,
            search_filter='(objectClass=user)',
            attributes=['sAMAccountName', 'displayName'],
            search_scope='SUBTREE',
            time_limit=timeout
        )

        # if conn.result['result'] != 0:
        #     logger.error(f"Ошибка LDAP: {conn.result['description']} ({conn.result['message']})")
        #     return users

        # Обработка результатов
        for entry in conn.entries:
            user_data = {attr: entry[attr].values for attr in entry}
            users.append(user_data)

        logger.info(f"Найдено {len(users)} пользователей")

    except LDAPSocketOpenError as e:
        logger.error(f"Не удалось подключиться к серверу: {e}")
    except LDAPBindError as e:
        logger.error(f"Ошибка аутентификации Kerberos: {e}")
        logger.error("Проверьте: 1) наличие Kerberos-билета (klist); 2) корректность realm")
    # except gssapi.exceptions.GSSError as e:
    #     logger.error(f"Ошибка GSSAPI: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {type(e).__name__}: {e}")

    finally:
        if conn and conn.bound:
            conn.unbind()
            logger.info("Соединение закрыто")

    return users

# Пример использования
if __name__ == '__main__':
    # Параметры подключения
    SERVER = DC_SERVER
    BASE_OU = SEARCH_BASE
    REALM = DOMAIN  # ваш Kerberos realm


    # Атрибуты для извлечения
    ATTRIBUTES = [
        'sAMAccountName',
        'userPrincipalName',
        'displayName',
        'mail',
        'department'
    ]

    # Вызов функции
    users = get_users_from_ou_kerberos(
        server_address=SERVER,
        base_ou=BASE_OU,
        attributes=ATTRIBUTES,
        timeout=30,
        connect_timeout=10,
        realm=REALM
    )

    # Вывод результатов
    for user in users:
        print(user)

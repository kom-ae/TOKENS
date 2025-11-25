from typing import List, Dict, Optional
from ldap3 import Server, Connection, SASL, GSSAPI
from ldap3.core.exceptions import LDAPBindError, LDAPSocketOpenError
# import winkerberos as kerberos
import logging


from constants import DC_SERVER, DOMAIN, LDAP_PORT, SEARCH_BASE, LDAP_CON_TIMEOUT, LDAP_SEARCH_TIMEOUT

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_users_from_ou_kerberos() -> List[Dict]:
    """Получить пользователей из OU через Kerberos‑аутентификацию."""
    users = []
    try:
        server = Server(
            DC_SERVER,
            port=LDAP_PORT,
            use_ssl=False,
            get_info='NO_INFO',
            connect_timeout=LDAP_CON_TIMEOUT
        )

        conn = Connection(
            server,
            authentication=SASL,
            sasl_mechanism=GSSAPI,
            auto_bind=True,
            read_only=True,
            raise_exceptions=False,

        )

        # Проверяем, кто мы
        print("Аутентифицирован как:", conn.extend.standard.who_am_i())

        conn.search(
            search_base=SEARCH_BASE,
            search_filter='(objectClass=user)',
            attributes=['sAMAccountName', 'cn', 'description'],
            search_scope='SUBTREE',
            time_limit=LDAP_SEARCH_TIMEOUT
        )

        if conn.result['result'] != 0:
            logger.error(f"Ошибка LDAP: {conn.result['description']} ({conn.result['message']})")
            return users

        # Обработка результатов
        for entry in conn.entries:
            # user_data = {attr: entry[attr].value for attr in entry.entry_attributes}
            user_data = {
                'cn': entry.cn.value.lower(),
                'description': entry.description.value,
                'sAMAccountName': entry.sAMAccountName.value
                  }
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

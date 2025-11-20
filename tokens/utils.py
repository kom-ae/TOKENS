from PyKCS11 import PyKCS11Lib

from constants import BLACK_LIST_TOKENS, LIST_LIBS
from .tokens import Token, tokens_classes


def get_slots(pkcs11: PyKCS11Lib) -> list:
    return pkcs11.getSlotList(tokenPresent=True)


def get_pkcs(lib: str) -> PyKCS11Lib:
    pkcs11 = PyKCS11Lib()
    return pkcs11.load(lib)


def get_tokens():
    tokens: dict[str, Token] = {}
    for lib in LIST_LIBS:
        pkcs11: PyKCS11Lib = get_pkcs(lib)
        slots: list = get_slots(pkcs11)
        for slot in slots:
            info = pkcs11.getTokenInfo(slot)
            serial_num = str(info.serialNumber).strip()
            if serial_num in BLACK_LIST_TOKENS:
                continue
            model = str(info.model).strip()
            token = tokens_classes.get(model)

            if token is None:
                return
            tokens[serial_num] = token(
                    lib,
                    serial_num,
                    info.ulMinPinLen,
                    str(info.label).strip(),
                    slot,
                )
        pkcs11.unload()
    return tokens


# def open_session(slot: int, pkcs11: PyKCS11Lib,  flags: int = 0) -> PyKCS11.Session:
#     return pkcs11.openSession(slot, flags)


# def session_login_admin(session: PyKCS11.Session) -> None:
#     for pin in LIST_PIN_ADMIN:
#         try:
#             session.login(pin, CKU_SO)
#             return pin
#         except PyKCS11Error:
#             continue
#     # session.closeSession()
#     return False


# def session_login_user(session: PyKCS11.Session) -> None:
#     try:
#         session.login(TEMP_USER_PIN, CKU_USER)
#     except PyKCS11Error:
#         print('Логин пользователя не прошел!')
#     except Exception as err:
#         print(str(err))


# def set_all_pin(session: PyKCS11.Session, old_pin: str) -> None:
#     try:
#         # проверить значение на минимум 6 символов
#         session.initPin(TEMP_USER_PIN)
#     except PyKCS11Error as err:
#         print(str(err))
#     try:
#         session.setPin(old_pin, PIN_ADMIN)
#     except PyKCS11Error as err:
#         print(str(err))


# def session_logout_close(session: PyKCS11.Session) -> None:

#     try:
#         info = session.getSessionInfo()
#     except PyKCS11Error as err:
#         if err.args[0] in (CKR_SESSION_HANDLE_INVALID, CKR_SESSION_CLOSED):
#             print('Сессия уже закрыта')
#         return
#     if info.state not in (CKS_RO_PUBLIC_SESSION, CKS_RW_PUBLIC_SESSION):
#         session.logout()
#     session.closeSession()

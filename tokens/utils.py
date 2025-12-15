from pathlib import Path
from PyKCS11 import PyKCS11Lib

from constants import BLACK_LIST_TOKENS, LIST_LIBS
from .tokens import Token, tokens_classes


def get_slots(pkcs11: PyKCS11Lib) -> list:
    """Вернуть номера слотов с токенами."""
    return pkcs11.getSlotList(tokenPresent=True)


def get_pkcs(lib: str) -> PyKCS11Lib:
    """Вернуть объект с загруженной библиотекой, для работы с токеном."""
    pkcs11 = PyKCS11Lib()
    return pkcs11.load(lib)


def get_tokens() -> dict[str, Token]:
    """Вернуть подключенные токены."""
    tokens: dict[str, Token] = {}
    for lib in LIST_LIBS:
        if not Path(lib).is_file():
            raise FileNotFoundError(f'Библиотека {lib} не найдена.')
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

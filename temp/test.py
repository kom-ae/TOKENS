import ctypes

import PyKCS11
from PyKCS11 import PyKCS11Lib
from PyKCS11 import CKA, CKO, PyKCS11Error
from PyKCS11.constants import (CKF_RW_SESSION, CKF_SERIAL_SESSION, CKR_OK,
                               CKR_PIN_INVALID, CKR_SESSION_CLOSED,
                               CKR_SESSION_HANDLE_INVALID,
                               CKR_USER_NOT_LOGGED_IN, CKS_RO_PUBLIC_SESSION,
                               CKS_RO_USER_FUNCTIONS, CKS_RW_PUBLIC_SESSION,
                               CKS_RW_USER_FUNCTIONS, CKU_SO, CKU_USER)
from PyKCS11.LowLevel import CPKCS11Lib

from constants import (BLACK_LIST_TOKENS, LIST_LIBS, LIST_PIN_ADMIN, PIN_ADMIN,
                       TEMP_USER_PIN, TOKEN_CONF)
from tokens import RutokenLite, RutokenS, tokens_classes, Token, JaCartaLaser

# # class CPKCS11Lib_CT(CPKCS11Lib):

# #     def __init___(self):
# #         super.__init__()
# #         self.lib.C_InitToken.restype = ctypes.c_ulong
# #         self.lib.C_InitToken.argtypes = [
# #             ctypes.c_ulong,                    # slot_list     (CK_SLOT_ID)
# #             ctypes.POINTER(ctypes.c_byte),     # sopin         (CK_BYTE_PTR)
# #             ctypes.c_ulong,                    # sopinlen      (CK_ULONG)
# #             ctypes.POINTER(ctypes.c_byte * 32) # label         (CK_BYTE_PTR)
# #         ]

# #     def C_InitToken(self, slotID, c_so_pin, c_pin_len, c_label):
# #         return _LowLevel.CPKCS11Lib_C_InitToken(self, slotID, pin, pLabel)


# class PKCS_LIB(PyKCS11_ORIG.PyKCS11Lib):

#     def __init__(self, libpath):
#         super().__init__()
#         self.lib_2 = ctypes.CDLL(libpath)

#         # C_InitToken
#         self.lib_2.C_InitToken.restype = ctypes.c_ulong
#         self.lib_2.C_InitToken.argtypes = [
#             ctypes.c_ulong,                    # slot_list     (CK_SLOT_ID)
#             ctypes.POINTER(ctypes.c_byte),     # sopin         (CK_BYTE_PTR)
#             ctypes.c_ulong,                    # sopinlen      (CK_ULONG)
#             ctypes.POINTER(ctypes.c_byte * 32)  # label         (CK_BYTE_PTR)
#         ]

#         # self.lib_2.C_InitToken.restype = ctypes.c_ulong
#         # self.lib_2.C_InitToken.argtypes = [
#         #     ctypes.c_int,                    # slot_list     (CK_SLOT_ID)
#         #     str,     # sopin         (CK_BYTE_PTR)
#         #     int,                    # sopinlen      (CK_ULONG)
#         #     str  # label         (CK_BYTE_PTR)
#         # ]

#     def initToken(self, slot, pin, label):
#         """
#             C_InitToken

#             :param slot: slot number returned by :func:`getSlotList`
#             :type slot: integer
#             :param pin: Security Officer's initial PIN
#             :param label: new label of the token
#         """

#         if len(label) > 32:
#             raise RuntimeError(
#                 'Label cannot be greater than 32, got: {}'.format(len(label)))

#         label = label.rjust(32, chr(ord(' ')))
#         c_label = (ctypes.c_byte * len(label)).from_buffer_copy(label.encode())

#         c_pin_len = ctypes.c_ulong(len(pin))

#         c_so_pin = (ctypes.c_byte * len(pin)).from_buffer_copy(pin.encode())

#         rv = self.lib_2.C_InitToken(slot, c_so_pin, len(pin), c_label)
#         # rv = self.lib_2.C_InitToken(slot, c_so_pin, c_pin_len, c_label)
#         if rv != CKR_OK:
#             raise RuntimeError(rv)

#     #     # pin1 = ckbytelist(pin)
#     #     # rv = self.lib.C_InitToken(slot, pin1, label)
#     #     # if rv != CKR_OK:
#     #     #     raise PyKCS11Error(rv)


def get_slots(pkcs11: PyKCS11Lib) -> list:
    return pkcs11.getSlotList(tokenPresent=True)


def get_pkcs(lib: str) -> PyKCS11Lib:
    pkcs11 = PyKCS11Lib()
    return pkcs11.load(lib)


def open_session(slot: int, pkcs11: PyKCS11Lib,  flags: int = 0) -> PyKCS11.Session:
    return pkcs11.openSession(slot, flags)


def session_login_admin(session: PyKCS11.Session) -> None:
    for pin in LIST_PIN_ADMIN:
        try:
            session.login(pin, CKU_SO)
            return pin
        except PyKCS11Error:
            continue
    # session.closeSession()
    return False


def session_login_user(session: PyKCS11.Session) -> None:
    try:
        session.login(TEMP_USER_PIN, CKU_USER)
    except PyKCS11Error:
        print('Логин пользователя не прошел!')
    except Exception as err:
        print(str(err))


def set_all_pin(session: PyKCS11.Session, old_pin: str) -> None:
    try:
        # проверить значение на минимум 6 символов
        session.initPin(TEMP_USER_PIN)
    except PyKCS11Error as err:
        print(str(err))
    try:
        session.setPin(old_pin, PIN_ADMIN)
    except PyKCS11Error as err:
        print(str(err))


def session_logout_close(session: PyKCS11.Session) -> None:

    try:
        info = session.getSessionInfo()
    except PyKCS11Error as err:
        if err.args[0] in (CKR_SESSION_HANDLE_INVALID, CKR_SESSION_CLOSED):
            print('Сессия уже закрыта')
        return
    if info.state not in (CKS_RO_PUBLIC_SESSION, CKS_RW_PUBLIC_SESSION):
        session.logout()
    session.closeSession()


def run():
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
    for sn, token in tokens.items():
        label = 'test1'
        user_pin = '456789'
        token.format(user_pin, label)
        # print(f'{sn} - {result.stdout}')
            # # label = label.rjust(32, chr(ord(' ')))
            # # c_label = (ctypes.c_byte * len(label)
            # #            ).from_buffer_copy(label.encode())

            # # c_pin_len = ctypes.c_ulong(len(soPin))

            # # c_so_pin = (ctypes.c_byte * len(soPin)
            # #             ).from_buffer_copy(soPin.encode())

            # pkcs11.initToken(slot, soPin, label)
            # session = open_session(slot, pkcs11, CKF_RW_SESSION)
            # if curent_admin_pin := session_login_admin(session):
            #     set_all_pin(session, curent_admin_pin)
            #     # gg = session.get_key(label='aes256')
            #     dd = session.findObjects()
            #     ff = pkcs11.getMechanismList(slot)
            #     session_logout_close(session)
            #     # pkcs11.initToken(slot, curent_admin_pin, 'rrrrrrrrrr')
            #     pkcs11.getTokenInfo(slot)
            # # session = open_session(slot, pkcs11, CKF_RW_SESSION)
            # # # session_login_user(session)
            # # session.login('456789')
            # # template = [(PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),
            # #             ]

            # # obj = session.findObjects()
            # # session_logout_close(session)


run()
# info = pkcs11.getInfo()
# print(info.manufacturerID)
# slots_i = pkcs11.getSlotInfo(0)
# slots_t = pkcs11.getTokenInfo()

# print('dd')

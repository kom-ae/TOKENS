import ctypes


class PyKCS11LibCustom:

    def __init__(self, libpath):
        self.lib = ctypes.CDLL(libpath)

        # C_InitToken
        self.lib.C_InitToken.restype = ctypes.c_ulong
        self.lib.C_InitToken.argtypes = [
            ctypes.c_ulong,                    # slot_list     (CK_SLOT_ID)
            ctypes.POINTER(ctypes.c_byte),     # sopin         (CK_BYTE_PTR)
            ctypes.c_ulong,                    # sopinlen      (CK_ULONG)
            ctypes.POINTER(ctypes.c_byte * 32)  # label         (CK_BYTE_PTR)
        ]

    def initToken(self, slot, pin, label):
        """Инициализация токена.

            :param slot: slot number
            :param pin: Security Officer's initial PIN
            :param label: new label of the token
        """

        if len(label) > 32:
            raise RuntimeError(
                'Label cannot be greater than 32, got: {}'.format(len(label)))

        label = label.ljust(32)
        c_label = (ctypes.c_byte * len(label)).from_buffer_copy(label.encode())

        c_so_pin = (ctypes.c_byte * len(pin)).from_buffer_copy(pin.encode())

        rv = self.lib.C_InitToken(slot, c_so_pin, len(pin), c_label)

        if rv != 0:
            raise RuntimeError(rv)

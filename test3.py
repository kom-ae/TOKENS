#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
'''
EXAMPLE CODE NOT INTENDED FOR PRODUCTION USE

Some Python code using ctypes to:
 - enumerate the slot list
 - find an empty slot
 - Initialize a token
 - Set the user pin
 - login/logout
 - create a CKO_DATA object
 - Retrieve that data object

Note that an existing Python wrapper is available:
 - https://github.com/danni/python-pkcs11
However, it doesn't support everything needed per the readme's tested compatibility
matrix. It would be best to upstream needed support there.

Below is a *very thin* wrapper using ctypes that will store and retrive the hardcoded
SECRET value.

Configuration:
  Set environment variable PKCS11_MODULE to point to the shared library
  Normal TPM2_PKCS11_* env variables work as well.

Limitations:
  This has a hardcoded label name on the token, so you can only run the script once and for
  subsequent runs you need to remove the hardcoded token name.
  tpm2_ptool can be used to find and remove the token.
'''

import os
from contextlib import contextmanager
import ctypes

from constants import BLACK_LIST_TOKENS

CKF_TOKEN_INITIALIZED = 0x00000400

CKF_SERIAL_SESSION = 0x00000004
CKF_RW_SESSION = 0x00000002

CKA_CLASS = 0x0
CKA_TOKEN = 0x1
CKA_PRIVATE = 0x2
CKA_LABEL = 0x3
CKA_APPLICATION = 0x10
CKA_VALUE = 0x11
CKA_OBJECT_ID = 0x12
CKA_MODIFIABLE = 0x170

CKO_DATA = 0x00

CKU_SO = 0
CKU_USER = 1

class CK_ATTRIBUTE(ctypes.Structure):
    _fields_ = [
        # don't use "type" as it's a Python reserved word, use kind
        ("kind",     ctypes.c_ulong),
        ("pValue",    ctypes.c_void_p),
        ("ulValueLen", ctypes.c_ulong)
     ]

class CK_VERSION(ctypes.Structure):
    _fields_ = [
        ("major", ctypes.c_ulong),
        ("minor", ctypes.c_ulong)
     ]

class CK_TOKEN_INFO(ctypes.Structure):
    _fields_ = [
        ("label",                ctypes.c_char * 32),
        ("manufacturer",         ctypes.c_char * 32),
        ("model",                ctypes.c_char * 16),
        ("serial_number",        ctypes.c_char * 16),
        ("flags",                ctypes.c_ulong),
        ("max_session_count",    ctypes.c_ulong),
        ("session_count",        ctypes.c_ulong),
        ("max_rw_session_count", ctypes.c_ulong),
        ("rw_session_count",     ctypes.c_ulong),
        ("max_pin_len",          ctypes.c_ulong),
        ("min_pin_len",          ctypes.c_ulong),
        ("total_public_memory",  ctypes.c_ulong),
        ("free_public_memory",   ctypes.c_ulong),
        ("total_private_memory", ctypes.c_ulong),
        ("free_private_memory",  ctypes.c_ulong),
        ("hardware_version",     CK_VERSION),
        ("firmware_version",     CK_VERSION),
        ("utc_time",             ctypes.c_char * 16),
    ]

class TPM2PKCS11(object):
    
    def __init__(self, libpath):
        # C_Initialize
        self.lib = ctypes.CDLL(libpath)        
        self.lib.C_Initialize.restype = ctypes.c_ulong
        self.lib.C_Initialize.argtypes = [ctypes.c_void_p]

        # C_GetSlotList
        self.lib.C_GetSlotList.restype = ctypes.c_ulong
        self.lib.C_GetSlotList.argtypes = [
            ctypes.c_byte,                  # token_present (CK_BYTE)
            ctypes.POINTER(ctypes.c_ulong), # slot_list     (CK_SLOT_ID_PTR)
            ctypes.POINTER(ctypes.c_ulong)  # count         (CK_ULONG_PTR)
        ]

        # C_GetTokenInfo
        self.lib.C_GetTokenInfo.restype = ctypes.c_ulong
        self.lib.C_GetTokenInfo.argtypes = [
            ctypes.c_ulong,               # slot_list     (CK_SLOT_ID)
            ctypes.POINTER(CK_TOKEN_INFO) # count         (CK_ULONG_PTR)
        ]

        # C_InitToken
        self.lib.C_InitToken.restype = ctypes.c_ulong
        self.lib.C_InitToken.argtypes = [
            ctypes.c_ulong,                    # slot_list     (CK_SLOT_ID)
            ctypes.POINTER(ctypes.c_byte),     # sopin         (CK_BYTE_PTR)
            ctypes.c_ulong,                    # sopinlen      (CK_ULONG)
            ctypes.POINTER(ctypes.c_byte * 32) # label         (CK_BYTE_PTR)
        ]

        # CK_RV C_OpenSession (CK_SLOT_ID slotID, CK_FLAGS flags, void *application, CK_NOTIFY notify, CK_SESSION_HANDLE *session);
        self.lib.C_OpenSession.restype = ctypes.c_ulong
        self.lib.C_OpenSession.argtypes = [
            ctypes.c_ulong,                    # session     (CK_SLOT_ID)
            ctypes.c_ulong,                    # flags       (CK_FLAGS)
            ctypes.POINTER(ctypes.c_void_p),   # application (CK_VOID_PTR)
            ctypes.POINTER(ctypes.c_void_p),   # notify cb   (CK_VOID_PTR)
            ctypes.POINTER(ctypes.c_ulong),    # session     (CK_ULONG)
        ]

        # CK_RV C_Login (CK_SESSION_HANDLE session, CK_USER_TYPE user_type, CK_BYTE_PTR pin, CK_ULONG pin_len) {
        self.lib.C_Login.restype = ctypes.c_ulong
        self.lib.C_Login.argtypes = [
            ctypes.c_ulong,                    # session     (CK_SESSION)
            ctypes.c_ulong,                    # user_type   (CK_USER_TYPE)
            ctypes.POINTER(ctypes.c_byte),     # pin         (CK_BYTE_PTR)
            ctypes.c_ulong,                    # pinlen      (CK_ULONG)
        ]
        
        # CK_RV C_Logout (CK_SESSION_HANDLE session)
        self.lib.C_Logout.restype = ctypes.c_ulong
        self.lib.C_Logout.argtypes = [
            ctypes.c_ulong,                    # session     (CK_SESSION)
        ]
        
        # C_InitPin (CK_SESSION_HANDLE session, CK_UTF8CHAR_PTR pin, CK_ULONG pin_len)
        self.lib.C_InitPIN.restype = ctypes.c_ulong
        self.lib.C_InitPIN.argtypes = [
            ctypes.c_ulong,                    # session     (CK_SESSION_HANDLE)
            ctypes.POINTER(ctypes.c_byte),     # pin         (CK_BYTE_PTR)
            ctypes.c_ulong,                    # pinlen      (CK_ULONG)
        ]

        # C_CloseSession (SK_SESSION_HANDLE session)
        self.lib.C_CloseSession.restype = ctypes.c_ulong
        self.lib.C_CloseSession.argtypes = [
            ctypes.c_ulong,                    # session     (CK_SESSION_HANDLE)
        ]

        # C_CreateObject (CK_SESSION_HANDLE session, CK_ATTRIBUTE *templ, CK_ULONG count, CK_OBJECT_HANDLE *object)
        self.lib.C_CreateObject.restype = ctypes.c_ulong
        self.lib.C_CreateObject.argtypes = [
            ctypes.c_ulong,                    # session     (CK_SESSION_HANDLE)
            ctypes.POINTER(CK_ATTRIBUTE),      # templ       (CK_ATTRIBUTE_PTR)
            ctypes.c_ulong,                    # count       (CK_SESSION_HANDLE)
            ctypes.POINTER(ctypes.c_ulong),    # count       (CK_OBJECT_HANDLE)
        ]

        # C_GetAttributeValue (CK_SESSION_HANDLE session, CK_OBJECT_HANDLE object, CK_ATTRIBUTE_PTR templ, CK_ULONG count)
        self.lib.C_GetAttributeValue.restype = ctypes.c_ulong
        self.lib.C_GetAttributeValue.argtypes = [
            ctypes.c_ulong,                    # session     (CK_SESSION_HANDLE)
            ctypes.c_ulong,                    # object      (CK_OBJECT_HANDLE)
            ctypes.POINTER(CK_ATTRIBUTE),      # templ       (CK_ATTRIBUTE_PTR)
            ctypes.c_ulong,                    # count       (CK_SESSION_HANDLE)
        ]

        # C_Finalize
        self.lib.C_Finalize.restype = ctypes.c_ulong
        self.lib.C_Finalize.argtypes = [ctypes.c_void_p]

        rv = self.lib.C_Initialize(None)
        if rv != 0:
            raise RuntimeError(rv)

    def GetSlotList(self, token_present=True):

        c_token_present = ctypes.c_byte(1 if token_present else 0)
       
        count = ctypes.c_ulong(0)

        # get the slot count
        rv = self.lib.C_GetSlotList(c_token_present, None, ctypes.byref(count))
        if rv != 0:
            raise RuntimeError(rv)

        c_slot_ids = (ctypes.c_ulong * count.value)()
        rv = self.lib.C_GetSlotList(c_token_present, c_slot_ids, ctypes.byref(count))
        if rv != 0:
            raise RuntimeError(rv)

        return list(c_slot_ids) 

    def GetTokenInfo(self, slotID):
        
        info = CK_TOKEN_INFO()
        
        rv = self.lib.C_GetTokenInfo(slotID, ctypes.byref(info))
        if rv != 0:
            raise RuntimeError(rv)

        return info

    def InitToken(self, slotID, soPin, label):
       
        if len(label) > 32:
            raise RuntimeError('Label cannot be greater than 32, got: {}'.format(len(label)))
    
        label = label.rjust(32, chr(ord(' ')))
        c_label = (ctypes.c_byte * len(label)).from_buffer_copy(label.encode())

        c_pin_len = ctypes.c_ulong(len(soPin))
    
        c_so_pin = (ctypes.c_byte * len(soPin)).from_buffer_copy(soPin.encode())
    
        rv = self.lib.C_InitToken(slotID, c_so_pin, c_pin_len, c_label)
        if rv != 0:
            raise RuntimeError(rv)

    def _CloseSession(self, c_session):

        rv = self.lib.C_CloseSession(c_session)
        if rv != 0:
            raise RuntimeError(rv)

    @contextmanager
    def OpenSession(self, slotID, flags= "r"):

        flag_value = CKF_SERIAL_SESSION
        
        if flags == "rw":
            flag_value =flag_value | CKF_RW_SESSION
        elif flags == "r":
            pass
        else:
            RuntimeError('Flags niether "r" or "rw", got: {}'.format(flags))   

        c_flags = ctypes.c_ulong(flag_value)

        c_session_handle = ctypes.c_ulong()

        rv = self.lib.C_OpenSession(slotID, c_flags, None, None, ctypes.byref(c_session_handle))
        if rv != 0:
            raise RuntimeError(rv)
        try:
            yield c_session_handle.value
        finally:
            self._CloseSession(c_session_handle)

    def Login(self, session, pin, user=CKU_USER):

        c_user = ctypes.c_ulong(user)
        c_session = ctypes.c_ulong(session)
        c_pin_len = ctypes.c_ulong(len(pin))
        c_pin = (ctypes.c_byte * len(pin)).from_buffer_copy(pin.encode())

        rv = self.lib.C_Login(c_session, c_user, c_pin, c_pin_len)
        if rv != 0:
            raise RuntimeError(rv)

    def Logout(self, session):

        c_session = ctypes.c_ulong(session)

        rv = self.lib.C_Logout(c_session)
        if rv != 0:
            raise RuntimeError(rv)

    def InitPIN(self, session, pin):

        c_session = ctypes.c_ulong(session)

        c_pin_len = ctypes.c_ulong(len(pin))
    
        c_pin = (ctypes.c_byte * len(pin)).from_buffer_copy(pin.encode())

        rv = self.lib.C_InitPIN(c_session, c_pin, c_pin_len)
        if rv != 0:
            raise RuntimeError(rv)

    @staticmethod
    def _to_raw_attrs(attrs):
        
        c_attrs = (CK_ATTRIBUTE * len(attrs))()

        for i, kind in enumerate(attrs):
            value = attrs[kind]
            if isinstance(value, str):
                c_len = ctypes.c_ulong(len(value))
                c_value = (ctypes.c_byte * len(value)).from_buffer_copy(value.encode())
            elif isinstance(value, bytes):
                c_len = ctypes.c_ulong(len(value))
                c_value = (ctypes.c_byte * len(value)).from_buffer_copy(value)
            elif isinstance(value, bool):
                c_len = ctypes.c_ulong(ctypes.sizeof(ctypes.c_byte))
                c_value = ctypes.c_byte(1 if value is True else 0)
            elif isinstance(value, int):
                c_len = ctypes.c_ulong(ctypes.sizeof(ctypes.c_ulong))
                c_value = ctypes.c_ulong(value)
            else:
                RuntimeError("Unknown type to handle, got: {}".format(type(value)))

            # assign
            c_attrs[i].kind = kind
            c_attrs[i].ulValueLen = c_len
            LP_c_byte_ptr = ctypes.pointer(c_value)
            c_attrs[i].pValue = ctypes.cast(LP_c_byte_ptr, ctypes.c_void_p)  

        return c_attrs

    @staticmethod
    def _to_non_allocated_raw_attrs(attrs):
        
        c_attrs = (CK_ATTRIBUTE * len(attrs))()

        for i, kind in enumerate(attrs):
            atype = attrs[kind]

            # We only support byte types, for now...
            if atype is bytes:
                pass
            else:
                raise RuntimeError("Unknown type to handle, got: {}".format(atype))

            # assign
            c_attrs[i].kind = kind

            c_len = ctypes.c_ulong(0)
            c_attrs[i].ulValueLen = c_len
            c_attrs[i].pValue = None  

        return c_attrs

    @staticmethod
    def _to_allocated_raw_attrs(c_attrs):
        
        for a in c_attrs:
            ulValueLen = a.ulValueLen
            b = ctypes.c_byte(ulValueLen)
            p = ctypes.pointer(b)
            a.pValue = ctypes.cast(p, ctypes.c_void_p)  

    @staticmethod
    def _raw_attrs_to_py_attrs(template, c_template):

        l = {}

        for i, k in enumerate(template):
            a = c_template[i]

            kind = a.kind
            ulValueLen = a.ulValueLen
            pValue = a.pValue
            
            print(f'kind={a.kind} ulValueLen={a.ulValueLen} pValue={a.pValue}')

            if k != kind: 
                raise RuntimeError("Attribute mismatch")

            atype = template[k]
            if atype is bytes:
                pass
            else:
                raise RuntimeError("Unknown type to handle, got: {}".format(atype))
           
            # Cast it to a pointer pointing to N bytes
            array_type = ctypes.c_byte * ulValueLen
            p = ctypes.cast(pValue, ctypes.POINTER(array_type))

            # get the contents
            c_value = p.contents
            value = bytes(c_value)

            # add it to the new templates
            l[kind] = value

        return l
            

    def CreateObject(self, session, template):
        
        c_len = ctypes.c_ulong(len(template))
        c_template = self._to_raw_attrs(template)
        c_obj_handle = ctypes.c_ulong(0)

        rv = self.lib.C_CreateObject(session, c_template, c_len, ctypes.byref(c_obj_handle))
        if rv != 0:
            raise RuntimeError(rv)
        
        return c_obj_handle.value

    def GetAttributeValue(self, session, obj_handle, template):

        c_len = ctypes.c_ulong(len(template))
        c_template = self._to_non_allocated_raw_attrs(template)
        c_obj_handle = ctypes.c_ulong(obj_handle)
        c_session = ctypes.c_ulong(session)

        # Call with non-allocated attrs to get the sizes needed
        rv = self.lib.C_GetAttributeValue(c_session, c_obj_handle, c_template, c_len, c_obj_handle)
        if rv != 0:
            raise RuntimeError(rv)

        self._to_allocated_raw_attrs(c_template)
        for a in c_template:
            print(f'kind={a.kind} ulValueLen={a.ulValueLen} pValue={a.pValue}')

        # Call with allocated attrs to get the values
        rv = self.lib.C_GetAttributeValue(c_session, c_obj_handle, c_template, c_len, c_obj_handle)
        if rv != 0:
            raise RuntimeError(rv)

        py_attrs = self._raw_attrs_to_py_attrs(template, c_template)
        return py_attrs

    def __del__(self):
        rv = self.lib.C_Finalize(None)
        if rv != 0:
            raise RuntimeError(rv)

def main():
    # try:
    #     LIB = os.environ['PKCS11_MODULE']
    # except KeyError:
    #     raise RuntimeError("Must define `PKCS11_MODULE' to run tests.")

    pkcs11 = TPM2PKCS11('C:\\Windows\\System32\\jcPKCS11-2.dll')

    slots = pkcs11.GetSlotList()

    use_slotID = 0
    for slotID in slots:
        info = pkcs11.GetTokenInfo(slotID)
        if info.serial_number.decode('utf-8') in BLACK_LIST_TOKENS:
            continue
        flags = info.flags
        use_slotID = slotID
        if flags & CKF_TOKEN_INITIALIZED == 0:
            print("Slot %d is unitialized" % (slotID))
            use_slotID = slotID
            break

    if use_slotID == 0:
        raise RuntimeError('No unitialized slot found')

    pkcs11.InitToken(use_slotID, "99612999", "mylabel")

    with pkcs11.OpenSession(use_slotID, "rw") as session:
        print(session)

        pkcs11.Login(session, "mysopin", CKU_SO)

        pkcs11.InitPIN(session, "myuserpin")

        pkcs11.Logout(session)

        pkcs11.Login(session, "myuserpin")

        SECRET = b'my data object'

        # Token is initialized, seal data and retrieve it       
        template = {
            CKA_CLASS       : CKO_DATA,
            CKA_TOKEN       : True,
            CKA_PRIVATE     : True,
            CKA_LABEL       : 'data object',
            CKA_MODIFIABLE  : True,
            CKA_APPLICATION : 'my application',
            CKA_OBJECT_ID   : '1234',
            CKA_VALUE       : SECRET
        }

        handle = pkcs11.CreateObject(session, template)
        print(f'object-handle={handle}')

        template2 = {
            CKA_VALUE : bytes
        }

        values = pkcs11.GetAttributeValue(session, handle, template2)
        
        v = values[CKA_VALUE]

        if v != SECRET:
            raise RuntimeError(f'Expected matching secrets, got: {v} != {SECRET}')

        print(f'Retrieved expected secret: "{v}"')

if __name__ == '__main__':
    main()

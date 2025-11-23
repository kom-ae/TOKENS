import pkcs11_custom
from pkcs11.constants import Attribute, ObjectClass, UserType
from pkcs11_custom import KeyType

from constants import JC_PKCS11_LIB, RT_PKCS11_LIB, BLACK_LIST_TOKENS


lib = pkcs11_custom.lib(JC_PKCS11_LIB)
# lib.C_Initialize()
slots = lib.C_GetSlotList(token_present=True)
slots = lib.get_slots(token_present=True)
token_new = lib.get_tokens()

for slot in slots:
    token = slot.get_token()
    # info = pkcs11.getTokenInfo(slot)
    if token.serial in BLACK_LIST_TOKENS:
        continue

    # token = slots[0].get_token()
# session = lib.openSession(0)

session = token.open(rw=True, so_pin='99612999')
# objs = session.get_objects({Attribute.CLASS: pkcs11.ObjectClass.SECRET_KEY})
session.init_token()
try:
    gg = session.get_key(label='kuznetsov_dv')
    print(gg)
except:
    pass
for obj in session.get_objects(
    {
        Attribute.CLASS: ObjectClass.CERTIFICATE,
        Attribute.KEY_TYPE: KeyType.GOSTR3411
    }
):
    print(obj)

print('ddd')

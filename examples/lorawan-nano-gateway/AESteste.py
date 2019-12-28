from Crypto.Cipher import AES
from Crypto.Hash import CMAC
from binascii import unhexlify, hexlify
from base64 import b64decode, b64encode
import struct
import sys

# Duas chaves de 32 bytes
nwk_swkey = unhexlify('3C74F4F40CAEA021303BC24284FCF3AF')
app_swkey = unhexlify('0FFA7072CC6FF69A102A0F39BEB0880F')

cmacHash = CMAC.new(nwk_swkey, ciphermod=AES)
AESCipher = AES.new(app_swkey, AES.MODE_CTR)
data = b'QH0UASYACAACHTzKYH83JoXnbg=='
cmacHash.update(data)
try:
    cmacHash.verify(nwk_swkey)
    print("Everything is fine")
except:
    print("Not authenticated msg")
    sys.exit()
# cmacHash.
print(data, AESCipher.decrypt( cmacHash.digest() ).decode('utf-8'))
print(struct.unpack(">l", unhexlify('2601147D'))[0])
# print(AESCipher.encrypt(data))
# AESCipher.decrypt(data)
#coding=utf-8

import sys
from binascii import unhexlify, hexlify
import threading

from GWThreads import recvThread, sendThread

if __name__ == "__main__":
    # Usa duas chaves para troca de mensagens
    nwk_swkey = unhexlify('3C74F4F40CAEA021303BC24284FCF3AF')
    app_swkey = unhexlify('0FFA7072CC6FF69A102A0F39BEB0880F')


    # data = '407d140126000800021d3cca607f372685e76e'
    t1 = threading.Thread(target = recvThread)
    t2 = threading.Thread(target = sendThread)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
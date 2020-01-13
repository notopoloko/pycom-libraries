import sys
from consts import *
from binascii import unhexlify, hexlify

from lorawanPkt import LoRaWANPkt

if __name__ == "__main__":
    nwk_swkey = unhexlify('3C74F4F40CAEA021303BC24284FCF3AF')
    app_swkey = unhexlify('0FFA7072CC6FF69A102A0F39BEB0880F')

    data = '407d140126000800021d3cca607f372685e76e'
    pkt = None

    # PHY_PAYLOAD
    try:
        pkt = LoRaWANPkt(data, nwk_swkey, app_swkey)
    except ValueError:
        sys.exit()

    print('Mtype: ' + str( pkt.getMType() ) + ' -> ' + stringMessageType[ pkt.getMType() ])
    print('Major: ' + str( pkt.getMajor() ))
    print('MIC code: ' + str( pkt.getMIC() ))

    print('\nDevice address: ' + str(pkt.getDevAddr()))
    print('Number of pkt: ' + str(pkt.getFCnt()))
    print('Adaptive Data Rate (ADR): ' + str(pkt.getADR()))
    print('ADRACKReq: ' + str(pkt.getADRACKReq()))
    print('ACK field: ' + str(pkt.getACK()))
    print('Is pending: ' + str(pkt.getFPending()))
    print('Tamanho do campo de opções: ' + str(pkt.getOptsLen()))
    print('Campo de opção MAC: ' + str(pkt.getFOpts()))

    print('\nPorta: ' + str(pkt.getPort()))
    print('Payload cifrado: ' + pkt.getFRMPayload())
    print('Payload decifrado: ' + pkt.getDecryptedPayload())
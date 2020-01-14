#coding=utf-8

from binascii import unhexlify
from consts import stringMessageType

def loraPktPrettyPrint(pkt):

    # try:
    #     pkt = LoRaWANPkt(data, nwk_swkey, app_swkey)
    # except ValueError:
    #     sys.exit()

    message = pkt.getDecryptedPayload()
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
    print('Payload decifrado: ' + message + ' -> ' + str(unhexlify(message)))
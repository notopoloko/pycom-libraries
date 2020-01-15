#coding=utf-8

from binascii import unhexlify
from consts import stringMessageType

def loraPktPrettyPrint(pkt):

	message = pkt.getDecryptedPayload()
	print('Mtype: ' + str( pkt.getMType() ) + ' -> ' + stringMessageType[ pkt.getMType() ])
	print('Major: ' + str( pkt.getMajor() ))
	print('MIC code: ' + str( pkt.getMIC() ))

	print('\nDevice address: ' + str( pkt.getDevAddr() )) # Big-endian
	print('Number of pkt: ' + str( pkt.getFCnt() )) # Big-endian
	print('Adaptive Data Rate (ADR): ' + str(pkt.getADR()))
	print('ADRACKReq: ' + str(pkt.getADRACKReq()))
	print('ACK field: ' + str(pkt.getACK()))
	print('Is pending: ' + str(pkt.getFPending()))
	print('Tamanho do campo de opcoes: ' + str(pkt.getOptsLen()))
	print('Campo de opcao MAC: ' + str(pkt.getFOpts()))

	print('\nPorta: ' + str(pkt.getPort()))
	print('Payload cifrado: ' + pkt.getFRMPayload())
	print('Payload decifrado: ' + message + ' -> ' + str(unhexlify(message)))
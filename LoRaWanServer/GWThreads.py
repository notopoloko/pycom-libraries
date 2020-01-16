#coding=utf-8

import sys
import socket
import json
import base64
from binascii import unhexlify

from lorawanPkt import LoRaWANPkt
from consts import *
from utils import loraPktPrettyPrint

def recvThread(NwkSKey, AppSKey):
	'''
	Thread para recepção de mensagens de dados e de status
	'''
	count = 1
	print('Iniciando thread de recepcao')
	# Cria socket UDP para recepção de mensagens
	recvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		recvSocket.bind(('', 13509))
	except OSError:
		print('Endereco utilizado. Saindo...')
		sys.exit()
	while True:
		data, host = recvSocket.recvfrom(1024)
		# print('Got: ' + str(data) + ' from: ' + str(host))
		if data[3] == PKT_PUSH_DATA:
			# Dados enviados para o servidor. 12 primeiros bytes são informações do GW
			try:
				message = json.loads(data[12:].decode('utf-8'))
				if 'stat' in message:
					ackMsg = bytes([PROTOCOL_VERSION]) + data[1:3] + bytes([PKT_PUSH_ACK])
					print('Mensagem de status recebida. Mandando ACK: ' + ackMsg.hex() + ' de ' + str(host))
					recvSocket.sendto(ackMsg, host)
				elif 'rxpk' in message:
					# print('RXPK pkt received' + '\n' + json.dumps(message, indent=4))
					for i in message['rxpk']:
						# data está em base64. Necessario transformar para hexadecimal
						print('\n\tMensagem do tipo RXPK recebida: ' + base64.b64decode(i['data']).hex())
						pkt = LoRaWANPkt( base64.b64decode(i['data']).hex(), NwkSKey, AppSKey )
						loraPktPrettyPrint(pkt)
						# Montar uma mensagem para transmissao numa das janelas 1 -> 1s, 2 -> 2s
						pkt.setDownlinkLoRaPktMsg(UNCONFIRMED_DATA_DOWN, pkt.getDevAddr(), False, False, False, 0, count, '', 2, 'Hello from network server', NwkSKey, AppSKey)
						# Janela 1
						downLinkMessage = dict()
						downLinkMessage['txpk'] = dict()
						# Assumindo dispositivos classe A
						downLinkMessage['txpk']['imme'] = True
						downLinkMessage['txpk']['tmst'] = i['tmst'] + 1000000
						downLinkMessage['txpk']['freq'] = 923.3
						# downLinkMessage['txpk']['rfch']
						downLinkMessage['txpk']['powe'] = 20
						downLinkMessage['txpk']['modu'] = 'LORA'
						downLinkMessage['txpk']['datr'] = i['datr']
						downLinkMessage['txpk']['codr'] = i['codr']
						downLinkMessage['txpk']['ipol'] = False
						downLinkMessage['txpk']['size'] = len(pkt.getLoRaPktMsg()) // 2
						downLinkMessage['txpk']['data'] = base64.b64encode(unhexlify(pkt.getLoRaPktMsg())).decode('utf-8')
						# print('We will send this json: \n' + json.dumps(downLinkMessage, indent=4))
						count += 1
						sendSocket.sendto( bytes([PROTOCOL_VERSION, token_h, token_l, PKT_PULL_RESP]) + json.dumps(downLinkMessage).encode('utf-8'), sendHost )
						# Janela 2
						downLinkMessage['txpk']['tmst'] = i['tmst'] + 2000000
						downLinkMessage['txpk']['freq'] = 923.3
						downLinkMessage['txpk']['datr'] = 'SF12BW500'

						sendSocket.sendto( bytes([PROTOCOL_VERSION, token_h, token_l, PKT_PULL_RESP]) + json.dumps(downLinkMessage).encode('utf-8'), sendHost )


				else:
					print('Outros tipos de mensagem precisam de tratamento...')

			except UnicodeDecodeError:
				print('JSON nao eh decodificavel')

			except Exception as e:
				print('Ocorreu erro' + str(e))



def sendThread():
	'''
	Thread para recepção de mensagens de downlink 
	'''
	print('Iniciando thread de transmissao...')
	# Cria socket UDP para transmissão de mensagens e atualização de status
	global sendSocket
	global sendHost
	global token_h
	global token_l
	sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		sendSocket.bind(('', 13510))
	except OSError:
		print('Endereco utilizado. Saindo...')
		sys.exit()
	while True:
		data, sendHost = sendSocket.recvfrom(64)
		token_h = data[1]
		token_l = data[2]
		# print('Got: ' + str(data) + ' from: ' + str(sendHost))
		if data[3] == PKT_PULL_DATA:
			# Mandando infomacao do GW para o servidor de aplicacao. Necessario mandar um ACK
			# com os tokens corretos
			print('Mensagem com informacao de token recebida: ' + data[1:3].hex() + ' de ' + str(sendHost))
			ackMsg = bytes([PROTOCOL_VERSION]) + data[1:3] + bytes([PKT_PULL_ACK])
			sendSocket.sendto(ackMsg, sendHost)
		elif data[3] == PKT_TX_ACK:
			print('Ack recebido')
		else:
			print('Outros tipos de mensagem precisam de tratamento 2...')

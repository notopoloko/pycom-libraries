#coding=utf-8

import sys
import socket
import json
import base64

from lorawanPkt import LoRaWANPkt
from consts import *
from utils import loraPktPrettyPrint

def recvThread(NwkSKey, AppSKey):
	'''
	Thread para recepção de mensagens de dados e de status
	'''
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
				else:
					print('Outros tipos de mensagem precisam de tratamento...')

			except UnicodeDecodeError:
				print('JSON nao eh decodificavel')



def sendThread():
	'''
	Thread para recepção de mensagens de downlink 
	'''
	print('Iniciando thread de transmissao...')
	# Cria socket UDP para transmissão de mensagens e atualização de status
	sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		sendSocket.bind(('', 13510))
	except OSError:
		print('Endereco utilizado. Saindo...')
		sys.exit()
	while True:
		data, host = sendSocket.recvfrom(64)
		# print('Got: ' + str(data) + ' from: ' + str(host))
		if data[3] == PKT_PULL_DATA:
			# Mandando infomacao do GW para o servidor de aplicacao. Necessario mandar um ACK
			# com os tokens corretos
			print('Mensagem com informacao de token recebida: ' + data[1:3].hex() + ' de ' + str(host))
			ackMsg = bytes([PROTOCOL_VERSION]) + data[1:3] + bytes([PKT_PULL_ACK])
			sendSocket.sendto(ackMsg, host)
		else:
			print('Outros tipos de mensagem precisam de tratamento 2...')

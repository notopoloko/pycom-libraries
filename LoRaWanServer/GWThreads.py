#coding=utf-8

import sys
import socket
import json

from lorawanPkt import LoRaWANPkt
from consts import *

def recvThread():
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
    i = 100
    while i >= 0:
        data, host = recvSocket.recvfrom(256)
        # print('Got: ' + str(data) + ' from: ' + str(host))
        if data[3] == PKT_PUSH_DATA:
            # Dados enviados para o servidor. 12 primeiros bytes são informações do GW
            try:
                message = json.loads(data[12:].decode('utf-8'))
                if 'stat' in message:
                    ackMsg = bytes([PROTOCOL_VERSION]) + data[1:3] + bytes([PKT_PUSH_ACK])
                    print('Mensagem de status recebida. Mandando ACK: ' + ackMsg.hex() + ' de ' + str(host))
                    recvSocket.sendto(ackMsg, host)
                else:
                    print('Outros tipos de mensagem precisam de tratamento...')
            except UnicodeDecodeError:
                print('JSON nao eh decodificavel')
        i -= 1

    

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
    i = 100
    while i >= 0:
        data, host = sendSocket.recvfrom(64)
        print('Got: ' + str(data) + ' from: ' + str(host))
        i -= 1
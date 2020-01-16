#coding=utf-8

from Crypto.Hash import CMAC
from Crypto.Cipher import AES
from binascii import unhexlify, hexlify
from math import ceil
import base64
from utils import loraPktPrettyPrint
from consts import *

# PHY_PAYLOAD
# bytes         1       1..M         4
# Significado   MHDR    MAC_PAYLOAD  MIC

class LoRaWANPkt(object):
	def __init__(self, loraPkt: str, NwkSKey: bytes, AppSKey: bytes):
		try:
			int(loraPkt, 16)
			self.__loraPkt = loraPkt
			self.__NwkSKey = NwkSKey
			self.__AppSKey = AppSKey

			# Campos do cabeçalho da camada MAC
			self.__Mtype = 0
			self.__RFU = 0
			self.__Major = 0

			self.__MHDR = self.__getMHDR()

			self.__MACPayload = self.__getMACPayload()

			self.__MIC = ''
			self.__getMIC()

			# Campos do cabeçalho de frame
			self.__DevAddrHex = ''
			self.__FCnt = 0

			# Campos de FCtrl
			self.__FCtrl = 0
			self.__ADR = 0
			self.__ADRACKREQ = 0
			self.__RFU = 0
			self.__ACK = 0
			self.__FPending = 0
			self.__FOptsLen = 0
			self.__FOpts = ''
			self.__getFHDR()
			
			# Campo de porta da mensagem
			self.__FPort = 0
			self.__getFPort()

			# Payload da mensagem
			self.__FRMPayload = ''
			self.__getFRMPayload()

			# Checa integridade
			self.__checkMIC()

			# Decifra payload
			self.__FRMPayloadDecrypted = ''
			self.__decryptPayload()

		except ValueError as ve:
			print('Construtor esta esperando uma string em hexadecimal', ve)
			raise ve

	def setDownlinkLoRaPktMsg(self, MType: int, DevAddr: str, ADR: bool, ACK: bool, FPending: bool, FOptsLen: int, FCnt: int, FOpts: str, FPort: int, FRMPayload: str, NwkSKey: bytes, AppSKey: bytes):
		# Checagem de parametros
		if MType < 0 or MType > 5 or MType % 2 != 1:
			raise ValueError('Parametro MType deve estar na faixa [0 - 5] e deve ser do tipo downlink')
		try:
			int(DevAddr, 16)
		except ValueError:
			raise ValueError('Parametro DevAddr deve ser uma string em hexadecimal')

		# Forma cabecalho MHDR (MType | RFU | Major)
		self.__loraPkt = ''
		self.__loraPkt += hex( MType << 5 )[2:]

		# Forma o cabecalho FHDR (DevAddr | FCtrl | FCnt | FOpts)
		# FCtrl = (ADR | RFU | ACK | FPending | FOptsLen)
		self.__loraPkt += ( bytes.fromhex(DevAddr) [::-1] ).hex() # Little-endian
		FCtrl = 0
		# Check ADR e RFU
		if ADR:
			FCtrl += 1
		FCtrl << 2
		# Check ACK
		if ACK:
			FCtrl += 1
		FCtrl << 1
		# Check FPending
		if FPending:
			FCtrl += 1
		FCtrl << 1
		# Soma com o OptsLen
		FCtrl += FOptsLen
		# Contatena FCtrl com FCnt
		self.__loraPkt += '{:02x}'.format(FCtrl) + '{:04x}'.format(FCnt << 8)
		if FOptsLen > 0:
			self.__loraPkt += FOpts
		# Adiciona porta
		self.__loraPkt += '{:02x}'.format(FPort) # Little-endian
		# Cifrar a mensagem antes de calcular o MIC
		# Necessario saber o tamanho do payload
		payloadSize = len(FRMPayload)
		# Checa qual chave usar
		if FPort == 0:
			crypto = AES.new(NwkSKey, AES.MODE_ECB)
		else:
			crypto = AES.new(AppSKey, AES.MODE_ECB)
		# Forma os blocos para decifrar a mensagem de acordo com a especificacao 1.0.2
		# S = S1 | S2 | S3 ...
		numOfBlocks = ceil(len(FRMPayload) / 16)
		S = bytes()
		i = 1
		while i <= numOfBlocks:
			# Cria os blocos para decifrar a mensagem
			Stemp = bytes()
			Stemp += bytes.fromhex('0100000000')
			# Insere o byte de direcao
			if MType % 2 == 0:
				# É uma mensagem de uplink
				Stemp += bytes.fromhex('00')
			else:
				# É uma mensagem de downlink
				Stemp += bytes.fromhex('01')
			# Insere o endereco do dispositivo
			Stemp += bytes.fromhex(DevAddr)[::-1]
			# Insere o contador
			Stemp += FCnt.to_bytes(2, 'little')
			# Insere os dois bytes mais significativos + byte zerado. Por enquanto assumindo 0
			Stemp += bytes.fromhex('000000')
			# Insere o numero do bloco
			Stemp += i.to_bytes(1, 'big')
			# Cifra o bloco
			S += crypto.encrypt(Stemp)
			i += 1
		# Completa o tamanho da mensagem com padding de zeros
		payload = str.encode( FRMPayload )
		if payloadSize % 16 != 0:
			payload = payload.ljust( 16 - (payloadSize % 16) + payloadSize , bytes([0x00]))

		# Faz um XOR entre S e o payload para cifrar a mensagem original
		encripted = [ a ^ b for (a,b) in zip(payload, S) ][0:payloadSize]
		self.__loraPkt += ''.join('{:02x}'.format(x) for x in encripted)
		# Calcula MIC e coloca no final da mensagem
		# Gera bloco B0
		B0 = bytes.fromhex('4900000000')
		# Insere direcao da mensagem
		if MType % 2 == 0:
			# UpLink Msg
			B0 += bytes.fromhex('00')
		else:
			# Downlink Msg
			B0 += bytes.fromhex('01')
		# Insere endereco do dispositivo
		B0 += bytes.fromhex(DevAddr)[::-1]
		# Insere o contador
		B0 += FCnt.to_bytes(2, 'little')
		# Insere os dois bytes mais significaticos. Por enquanto assumindo 0
		B0 += bytes.fromhex('0000')
		# Insere 0x00 + tamanho da mensagem
		B0 += (len(self.__loraPkt) // 2).to_bytes(2, 'big')
		# Retira MIC da mensagem e adiciona B0 -> B0 | MSG
		__Message = unhexlify( self.__loraPkt)
		__Message = B0 + __Message

		# Cria um Hash
		cobj = CMAC.new(self.__NwkSKey, ciphermod=AES)
		cobj.update(__Message)
		# Integridade checada com os 4 primeiros bytes
		self.__loraPkt += cobj.hexdigest()[0:8]
		# Atualiza campos da mensagem
		self.__NwkSKey = NwkSKey
		self.__AppSKey = AppSKey

		self.__MHDR = self.__getMHDR()

		self.__MACPayload = self.__getMACPayload()

		self.__getMIC()

		self.__getFHDR()

		self.__getFPort()

		self.__getFRMPayload()

		self.__checkMIC()

		self.__decryptPayload()

	def __getMACPayload(self):
		try:
			return self.__loraPkt[2:-8]
		except IndexError:
			print('Mensagem LoRa não contém Payload')

	def __getMHDR(self) -> str:
		try:
			_MHDR_field = int(self.__loraPkt[0] + self.__loraPkt[1], 16)
			self.__Mtype = _MHDR_field >> 5
			self.__RFU = (_MHDR_field & 0x1F) >> 2
			self.__Major = _MHDR_field & 0x03
			return _MHDR_field
		except IndexError:
			print('Mensagem LoRa nao contem informacao de cabecalho')

	# def __decode_MHDR_field(self, MHDR_field: str):
	#     try:
	#         _MHDR_field = int (MHDR_field, 16)
	#         self.__Mtype = _MHDR_field >> 5
	#         self.__RFU = (_MHDR_field & 0x1F) >> 2
	#         self.__Major = _MHDR_field & 0x03

	#         print('Mtype: ' + str(self.__Mtype) + ' -> ' + stringMessageType[self.__Mtype])
	#         print('RFU: ' + str( self.__RFU ))
	#         print('Major: ' + str( self.__Major ))
	#     except ValueError:
	#         print('É experado um hexa no campo MHDR')

	def __getMIC(self):
		try:
			self.__MIC = self.__loraPkt[-8:] 
		except IndexError:
			print('Mensagem LoRa nao contem informacao MIC')

	def __getFHDR(self, verboose: bool = False): 
		try:
			self.__DevAddrHex = self.__MACPayload[0:8]

			self.__FCtrl = int(self.__MACPayload[8:10])
			self.__decodeFctrlField()
			self.__FCnt = int(self.__MACPayload[10:14], 16)
			self.__FOpts = self.__MACPayload[14:14 + self.__FOptsLen]
			# return self.__MACPayload[0:]
		except IndexError:
			print('Mensagem LoRa nao contem informacoes de cabecalho')

	def __decodeFctrlField(self):
		if self.__Mtype % 2 == 1:
			# Mensagem do tipo downlink
			self.__ADR = self.__FCtrl >> 7
			self.__RFU = self.__FCtrl & 0x7F >> 6
			self.__ACK = self.__FCtrl & 0x3F >> 5
			self.__FPending = self.__FCtrl & 0x1F >> 4
			self.__FOptsLen = self.__FCtrl & 0x0F
		else:
			self.__ADR = self.__FCtrl >> 7
			self.__ADRACKREQ = self.__FCtrl & 0x7F >> 6
			self.__ACK = self.__FCtrl & 0x3F >> 5
			self.__RFU = self.__FCtrl & 0x1F >> 4
			self.__FOptsLen = self.__FCtrl & 0x0F

	def __getFPort(self):
		try:
			# Pula informacoes de cabeçalho
			self.__FPort = int(self.__MACPayload[14 + self.__FOptsLen: 14 + self.__FOptsLen + 2], 16)
		except IndexError:
			print('A mensagem nao possui valor da porta.')

	def __getFRMPayload(self):
		try:
			self.__FRMPayload = self.__MACPayload[14 + self.__FOptsLen + 2: ]
		except IndexError:
			print('A mensagem nao possui payload')

	def __checkMIC(self):
		# Gera bloco B0
		B0 = bytes.fromhex('4900000000')
		# Insere direcao da mensagem
		if self.__Mtype % 2 == 0:
			# UpLink Msg
			B0 += bytes.fromhex('00')
		else:
			# Downlink Msg
			B0 += bytes.fromhex('01')
		# Insere endereco do dispositivo
		B0 += bytes.fromhex(self.__DevAddrHex)
		# Insere o contador
		B0 += self.__FCnt.to_bytes(2, 'big')
		# Insere os dois bytes mais significaticos. Por enquanto assumindo 0
		B0 += bytes.fromhex('0000')
		# Insere 0x00 + tamanho da mensagem
		B0 += (len(self.__loraPkt[:-8]) // 2).to_bytes(2, 'big')
		# Retira MIC da mensagem e adiciona B0 -> B0 | MSG
		__Message = unhexlify( self.__loraPkt[:-8])
		__Message = B0 + __Message
		# Cria um Hash
		cobj = CMAC.new(self.__NwkSKey, ciphermod=AES)
		cobj.update(__Message)
		# Integridade checada com os 4 primeiros bytes
		fullCMAC = cobj.hexdigest()[0:8]
		if fullCMAC == self.__MIC:
			print('\n\tA mensagem nao foi modificada. MIC esta batendo\n')
		else:
			print('\n\tA mensagem pode ter sido modificada. MIC nao esta batendo\n')

	def __decryptPayload(self):
		# Checa qual chave usar
		if self.__FPort == 0:
			crypto = AES.new(self.__NwkSKey, AES.MODE_ECB)
		else:
			crypto = AES.new(self.__AppSKey, AES.MODE_ECB)
		# Forma os blocos para decifrar a mensagem de acordo com a especificacao 1.0.2
		# S = S1 | S2 | S3 ...
		numOfBlocks = ceil(len(self.__FRMPayload) / (2*16))
		S = bytes()
		i = 1
		while i <= numOfBlocks:
			# Cria os blocos para decifrar a mensagem
			Stemp = bytes()
			Stemp += bytes.fromhex('0100000000')
			# Insere o byte de direcao
			if self.__Mtype % 2 == 0:
				# É uma mensagem de uplink
				Stemp += bytes.fromhex('00')
			else:
				# É uma mensagem de downlink
				Stemp += bytes.fromhex('01')
			# Insere o endereco do dispositivo
			Stemp += bytes.fromhex(self.__DevAddrHex)
			# Insere o contador
			Stemp += self.__FCnt.to_bytes(2, 'big')
			# Insere os dois bytes mais significativos. Por enquanto assumindo 0
			Stemp += bytes.fromhex('0000')
			# Insere um byte zerado
			Stemp += bytes.fromhex('00')
			# Insere o numero do bloco
			Stemp += i.to_bytes(1, 'big')
			# Cifra o bloco
			S += crypto.encrypt(Stemp)
			i += 1
		
		# Completa o tamanho da mensagem com padding de zeros
		payload = bytes.fromhex(self.__FRMPayload)
		if len(payload) % 16 != 0:
			payload = payload.ljust(16 - len(payload) % 16 + len(payload), bytes([0x00]))
		# print(len(payload), payload.hex(), padLen, S.hex())

		# Faz um XOR entre S e o payload pra resgatar a mensagem original
		decripted = [ a ^ b for (a,b) in zip(payload, S) ][0:(len(self.__FRMPayload) // 2)]
		self.__FRMPayloadDecrypted = ''.join('{:02x}'.format(x) for x in decripted)


	def getMType(self):
		'''
		Retorna um inteiro referente ao tipo da mensage
		JOIN_REQUEST = 0
		JOIN_ACCEPT  = 1
		UNCONFIRMED_DATA_UP = 2
		UNCONFIRMED_DATA_DOWN = 3
		CONFIRMED_DATA_UP = 4
		CONFIRMED_DATA_DOWN = 5
		'''
		return self.__Mtype

	def getMajor(self):
		'''
		Retorna o inteiro referente ao Major
		'''
		return self.__Major

	def getMIC(self):
		'''
		Return o valor hexadecimal do código
		'''
		return self.__MIC
	
	def getDevAddr(self):
		'''
		Retorna o endereço do dispositivo em hexadecimal
		'''
		return ( bytes.fromhex(self.__DevAddrHex) [::-1] ).hex()

	def getFCnt(self):
		'''
		Retorna um inteiro que se refere ao contador do pacote
		'''
		return self.__FCnt >> 8
	
	def getADR(self):
		'''
		Retorna o valor do bit Adaptive Data Rate
		'''
		return self.__ADR

	def getADRACKReq(self):
		'''
		Retorna o valor do bit referente ao ack do Adaptive Data rate
		'''
		return self.__ADRACKREQ

	def getACK(self):
		'''
		Retorna o valor do bit ACK do pacote
		'''
		return self.__ACK

	def getFPending(self):
		'''
		Retorna o valor do bit Pending (indica que ha mais dados para transmissão) do pacote
		'''
		return self.__FPending

	def getOptsLen(self):
		'''
		Retorna um inteiro com o tamanho do campo de opções
		'''
		return self.__FOptsLen

	def getFOpts(self) -> str:
		'''
		Retorna uma string em hexa do campo de opções
		'''
		return self.__FOpts

	def getPort(self) -> int:
		'''
		Retorna um inteiro contendo a porta do pacote
		'''
		return self.__FPort

	def getFRMPayload(self) -> str:
		'''
		Retorna um hexa com o payload cifrado
		'''
		return self.__FRMPayload

	def getDecryptedPayload(self) -> str:
		'''
		Retorna o hexa decifrado
		'''
		return self.__FRMPayloadDecrypted

	def getLoRaPktMsg(self) -> str:
		'''
		Retorna uma string em hexadecimal com a mensagem passada no construtor ou montada pelo metodo setDownlinkLoRaPktMsg
		'''
		return self.__loraPkt

if __name__ == "__main__":
	nwk_swkey = unhexlify('3C74F4F40CAEA021303BC24284FCF3AF')
	app_swkey = unhexlify('0FFA7072CC6FF69A102A0F39BEB0880F')

	# data = '407d140126000800021d3cca607f372685e76e'
	data = base64.b64decode('YH0UASYABAACtuCCHCAOsbrykSQJbCY6tqhCHcbIpi/FXZStnxs=').hex()
	# data = '407d140126000800021d3cca607f072383f23f'
	pkt = LoRaWANPkt(data, nwk_swkey, app_swkey)
	loraPktPrettyPrint(pkt)

	pkt.setDownlinkLoRaPktMsg(UNCONFIRMED_DATA_DOWN, '2601147D', False, False, False, 0, 8, '', 2, 'PKT #8', nwk_swkey, app_swkey)
	loraPktPrettyPrint(pkt)
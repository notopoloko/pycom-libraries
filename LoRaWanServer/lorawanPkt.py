from Crypto.Hash import CMAC
from Crypto.Cipher import AES
from binascii import unhexlify, hexlify
from math import ceil

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
            self.__Mtype: int = 0
            self.__RFU: int = 0
            self.__Major: int = 0

            self.__MHDR = self.__getMHDR()

            self.__MACPayload = self.__getMACPayload()

            self.__MIC: str = ''
            self.__getMIC()

            # Campos do cabeçalho de frame
            self.__DevAddrHex: str = ''
            self.__FCnt: int = 0

            # Campos de FCtrl
            self.__FCtrl: int = 0
            self.__ADR: int = 0
            self.__ADRACKREQ: int = 0
            self.__RFU: int = 0
            self.__ACK: int = 0
            self.__FPending: int = 0
            self.__FOptsLen: int = 0
            self.__FOpts: str = ''
            self.__getFHDR()
            
            # Campo de porta da mensagem
            self.__FPort: int = 0
            self.__getFPort()

            # Payload da mensagem
            self.__FRMPayload: str = ''
            self.__getFRMPayload()

            # Checa integridade
            self.__checkMIC()

            # Decifra payload
            self.__FRMPayloadDecrypted: str = ''
            self.__decryptPayload()

        except ValueError as ve:
            print('Construtor está esperando uma string em hexadecimal', ve)
            raise ve

    def setLoRaPkt(self, loraPkt: str):
        try:
            int(loraPkt, 16)
            self.loraPkt = loraPkt
        except ValueError as ve:
            print('Função setLoRaPkt está esperando uma string em hexadecimal')
            raise ve

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
            print('Mensagem LoRa não contém informação de cabeçalho')

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
            print('Mensagem LoRa não contém informação MIC')

    def __getFHDR(self, verboose: bool = False): 
        try:
            self.__DevAddrHex = self.__MACPayload[0:8]

            self.__FCtrl = int(self.__MACPayload[8:10])
            self.__decodeFctrlField()
            self.__FCnt = int(self.__MACPayload[10:14], 16)
            self.__FOpts = self.__MACPayload[14:14 + self.__FOptsLen]
            # return self.__MACPayload[0:]
        except IndexError:
            print('Mensagem LoRa não contém informações de cabeçalho')

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
        B0: bytes = bytes.fromhex('4900000000')
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
            print('\n\tA mensagem não foi modificada. MIC está batendo\n')
        else:
            print('\n\tA mensagem pode ter sido modificada. MIC não está batendo\n')

    def __decryptPayload(self):
        # Checa qual chave usar
        if self.__FPort == 0:
            crypto = AES.new(self.__NwkSKey, AES.MODE_ECB)
        else:
            crypto = AES.new(self.__AppSKey, AES.MODE_ECB)
        # Forma os blocos para decifrar a mensagem de acordo com a especificacao 1.0.2
        # S = S1 | S2 | S3 ...
        numOfBlocks = ceil(len(self.__FRMPayload) / (2*16))
        S: bytes = bytes()
        i = 1
        while i <= numOfBlocks:
            # Cria os blocos para decifrar a mensagem
            Stemp: bytes = bytes()
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
        payload: bytes = bytes.fromhex(self.__FRMPayload)
        payload = payload.ljust(16, bytes([0x00]))
        
        # print(len(payload), payload.hex(), padLen, S.hex())

        # Faz um XOR entre S e o payload pra resgatar a mensagem original
        decripted = [ chr(a ^ b) for (a,b) in zip(payload, S) ][0:(len(self.__FRMPayload) // 2)]
        print(decripted)
        # self.__FRMPayloadDecrypted = "".join(decripted)


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
        return self.__DevAddrHex

    def getFCnt(self):
        '''
        Retorna um inteiro que se refere ao contador do pacote
        '''
        return self.__FCnt
    
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
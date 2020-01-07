from consts import *

# PHY_PAYLOAD
# bytes         1       1..M         4
# Significado   MHDR    MAC_PAYLOAD  MIC

class LoRaWANPkt(object):
    def __init__(self, loraPkt: str):
        try:
            int(loraPkt, 16)
            self.__loraPkt = loraPkt

            # Campos do cabeçalho 
            self.__Mtype: int = 0
            self.__RFU: int = 0
            self.__Major: int = 0

            self.__getMHDR()

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
            

        except ValueError as ve:
            print('Construtor está esperando uma string em hexadecimal')
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

    def __getMHDR(self, verboose: bool = False) -> str:
        try:
            _MHDR_field = self.__loraPkt[0] + self.__loraPkt[1]
            if verboose:
                self.__decode_MHDR_field(_MHDR_field)
            return _MHDR_field
        except IndexError:
            print('Mensagem LoRa não contém informação de cabeçalho')

    def __decode_MHDR_field(self, MHDR_field: str):
        try:
            _MHDR_field = int (MHDR_field, 16)
            self.__Mtype = _MHDR_field >> 5
            self.__RFU = (_MHDR_field & 0x1F) >> 2
            self.__Major = _MHDR_field & 0x03

            print('Mtype: ' + str(self.__Mtype) + ' -> ' + stringMessageType[self.__Mtype])
            print('RFU: ' + str( self.__RFU ))
            print('Major: ' + str( self.__Major ))
        except ValueError:
            print('É experado um hexa no campo MHDR')

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
            return self.__MACPayload[0:]
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

    def getMType(self):
        return self.__Mtype

    def getMajor(self):
        return self.__Major

    def getMIC(self):
        return self.__MIC
    
    def getDevAddr(self):
        return self.__DevAddrHex

    def getFCnt(self):
        return self.__FCnt
    
    def funcname(self, parameter_list):
        pass
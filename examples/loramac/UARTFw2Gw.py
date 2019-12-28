from machine import UART
from network import LoRa
from time import sleep
import socket
import _thread
import sys

# Transmite da interface UART para LoRa
def UART2LoRa( unusedId ):
    global s
    global lock

    i = 1000
    while i >= 0:
        msg = uart.read(64)
        print("Ready to recv on UART")
        # Se houver mensagem na interface UART mandar via lora
        if msg != None:
            print('Mesagem recebida: ' + str(msg) + '. Mandando via LoRa')
            with lock:
                s.setblocking( True )
                s.send( msg )
                s.setblocking( False )
        # For debug purposes
        sleep(1)
        i -= 1
    print( 'Saindo da thread UART2LoRa' )
    # Sair silenciosamente
    _thread.exit()

# Recebe do LoRa e manda via UART
def LoRa2UART( unusedId ):
    global s
    global lock

    i = 1000
    # Bad
    while i >= 0:
        # sleep(2)
        with lock:
            data = s.recv(64)
        print("Ready to recv on LoRa")
        if len(data) != 0:
            print('Mensagem recebida: ' + str(data) + '. Mandando via UART')
            uart.write(data)
            # For debug purposes
        sleep(1)
        i -= 1
    print('Saindo da thread LoRa2UART')
    # Sair silenciosamente
    _thread.exit()

# if __name__ == 'main':
lora = LoRa( mode=LoRa.LORA, region=LoRa.US915, frequency=915600000, sf=9, bandwidth=LoRa.BW_500KHZ )

# create a raw LoRa socket
s = socket.socket( socket.AF_LORA, socket.SOCK_RAW )
s.setblocking( False )

uart = UART(1, 9600)
lock = _thread.allocate_lock()

_thread.start_new_thread( LoRa2UART, (1,))
_thread.start_new_thread( UART2LoRa, (2,))

input()
print('terminando programa')

sys.exit()
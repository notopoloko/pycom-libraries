import sys

from lorawanPkt import LoRaWANPkt

if __name__ == "__main__":
    data = '407d140126000800021d3cca607f372685e76e'
    pkt = None

    # PHY_PAYLOAD
    try:
        pkt = LoRaWANPkt(data)
    except ValueError:
        sys.exit()
    # print(pkt.getMHDR(True))
    # print(pkt.getMIC())
    # print(pkt.getMACPayload())
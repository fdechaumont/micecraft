'''
Created on 16 juin 2022

@author: Fab
'''



import socket
import logging


class LMTEventSender(object):

    def __init__(self, message ):

        UDP_IP = "127.0.0.1"
        UDP_PORT = 8551
        logging.info( f"Sending event to LMT {UDP_IP}:{UDP_PORT} : {message}" )
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(bytes(message, "utf-8"), (UDP_IP, UDP_PORT))


if __name__ == '__main__':
    
    
    print("Testing...")
    
    LMTEventSender("Test message on 127.0.0.1:8551 from UDP")

    print("Done")

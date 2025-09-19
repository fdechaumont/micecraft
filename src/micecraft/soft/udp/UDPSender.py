'''
Created on 21 janv. 2025

@author: Fab
'''
import socket

class UDPSender(object):


    def __init__(self, ip, port ):
        
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #s.bind(("127.0.0.1", 8551))        
        self.enabled = True
            
    def send(self , message ):
        
        #sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.sock.sendto(bytes( message  , "utf-8"), ( self.ip , self.port ))
        
    
        
        

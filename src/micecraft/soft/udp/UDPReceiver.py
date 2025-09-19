'''
Created on 21 janv. 2025

@author: Fab
'''
import socket
import threading
import atexit

class UDPReceiver(object):


    def __init__(self, ip, port ):
        
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #self.sock.setblocking(0)
        #s.bind(("127.0.0.1", 8551))
        self.listenerList = []
        self.enabled = True
        
        self.sock.bind(( self.ip, self.port ))
        #self.sock.setblocking( False )
        self.listeningThread = threading.Thread(target= self.socketListener ) 
        self.listeningThread.start()
        
        atexit.register(self.shutdown)
    
    
    def addListener(self , method ):
        self.listenerList.append( method )

    def removeListener(self , method ):
        self.listenerList.remove( method )
    
    def fireEvent(self , message, address ):
        for listener in self.listenerList:
            listener( message, address )
    
    def shutdown(self):
        self.enabled = False
    
    def socketListener(self):

        while( self.enabled ):
            #self.sock.settimeout(1.0)
            #message, address = self.sock.accept()
            
            # todo: change this so that it is non-blocking. Can't change it until it is protocol agnostic
            
            addr = self.sock.recvfrom(1024)            
            message = addr[0]
            address = addr[1]
            
            self.fireEvent(message, address)
        self.sock.close()
        print("UDPReceiver exits socket listener")
    
        
    
        
        

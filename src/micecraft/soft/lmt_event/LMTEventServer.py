'''
Created on 25 fev. 2021

@author: Fab
'''

import socket

if __name__ == '__main__':

    msg = str.encode("Hello Client!")
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 8551))
    print("UDP server listening...")
    
    while(True):
        addr = s.recvfrom(1024)
        message = addr[0]
        address = addr[1]        
        print( address, message )
        
        #s.sendto(msg, address)
        
        
    print("quit")
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
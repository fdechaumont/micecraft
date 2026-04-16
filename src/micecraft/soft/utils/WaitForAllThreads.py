'''
Created on 10 juil. 2025

@author: fabrice de chaumont
'''
import threading
from time import sleep

class WaitForAllThreads(object):

    def __init__(self ):
        
        print("--- remaining threads, waiting for finish...")
        while ( len( threading.enumerate() ) > 1 ): # MainThread included
            print("--- remaining threads, waiting for finish...")
            for thread in threading.enumerate(): 
                print(thread.name)
            sleep(1)
        
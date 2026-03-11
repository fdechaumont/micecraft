'''
Created on 20 sept. 2024

@author: Fab
'''
import threading
import random
import time

class ThreadTest(object):
    
    def __init__(self, ts):

        self.ts = ts
        
        self.tList = []
        
        for i in range( 4 ):
            t = threading.Thread(target=self.action )
            t.start()
            self.tList.append( t )
        
        
    def action(self):
        
        while True:
            
            self.ts.setImage( random.randint(0,2), random.randint(1,self.ts.nbCols), random.randint(1,self.ts.nbRows) )
            time.sleep( 0.05 )
        
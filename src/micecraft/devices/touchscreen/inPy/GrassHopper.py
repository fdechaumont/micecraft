'''
Created on 20 sept. 2024

@author: Fab
'''
import threading
import random
import math
import time

class GrassHopper(object):
    
    nb = 0

    def __init__(self, ts ):
                
        self.ts = ts
        
        self.scale = 0.2
        self.x= 1920/2
        self.y= 1080/2
        self.rotation = 360*random.random()
        self.rotationInertia = 0
        self.name = f"grasshopper{GrassHopper.nb}"
        GrassHopper.nb+=1
        
        self.enabled = True
        self.setBounds()

        self.ts.addDeviceListener( self.listener )

        self.thread = threading.Thread(target=self.animate )
        self.thread.start()
    
    def setBounds(self, xMin=100, yMin=100, xMax=1920-100, yMax=1080-100 ):
        self.xMin=xMin
        self.yMin=yMin
        self.xMax=xMax
        self.yMax=yMax  
        
    def listener(self, event):
        
        if "symbol xy touched" in event.description:
            name = event.data[0]
            if self.name == name:
                print( f"Grasshopper touched !")
                self.ts.removeXYImage( name )
                self.enabled=False
        
    def animate(self):        
        
        while self.enabled:
            
            vx = math.sin( math.radians( self.rotation+180 ) )
            vy = math.cos( math.radians( self.rotation+180 ) )
            
            self.x+= vx*10
            self.y+= vy*10
            self.rotationInertia += (random.random()-0.5) * 4
            self.rotationInertia *= 0.95
            self.rotation += self.rotationInertia
                    
            
            if self.x < self.xMin:
                self.x = self.xMin
            if self.x > self.xMax:
                self.x = self.xMax

            if self.y < self.yMin:
                self.y = self.yMin
            if self.y > self.yMax:
                self.y = self.yMax
                                        
            self.ts.setXYImage( self.name , 12, int(self.x) , int(self.y) , int(self.rotation), self.scale )
            
            time.sleep( 0.05 )
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
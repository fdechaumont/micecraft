'''
Created on 18 dec. 2023

@author: Fab
'''

from micecraft.devices.fed3.Fed3 import Fed3

if __name__ == '__main__':
    
    
    def listener( event ):
        if "nose poke" in event.description:
            fed.click()
            fed.feed()
        
    fed = Fed3( comPort="COM78", name="Fed 3 Test" )
    
    fed.addDeviceListener(listener)
    
    input("hit enter to stop experiment.")
    
    fed.shutdown()
    
    
            
        

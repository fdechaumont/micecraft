'''
Created on 20 déc. 2023

@author: Fab
'''

from time import sleep
import logging
import sys
from micecraft.devices.waterpump.WaterPump import WaterPump

if __name__ == '__main__':
    
    logging.basicConfig(level=logging.INFO )        
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    
    def listener( event ):
        print( event )
        
    pump = WaterPump( comPort="COM61" )   
    pump.addDeviceListener( listener ) 
    
    #pump.setDropParameters( 255 , 13, 0.02 )
    # pump 130: 255,12
    # pump 131: 255,13
    # 17: 0.03
    
    
    while True:
        print("1 : drop")
        print("2 : flush")
        print("3 : lightOn")
        print("4 : lightOff")
        print("5 : click")
        print("6 : 20 drops & flush")
        print("7 : test sequence")
        print("8 : 10 drops")
        print("9 : 1 big drop")
        
    
        a = input("choice:")
        
        if "1" in a:
            pump.deliverDrop( 1 )
            
        if "2" in a:
            pump.flush( 255 , 500 )
            
        if "3" in a:
            pump.lightOn( 255 )
            
        if "4" in a:
            pump.lightOff()
            
        if "5" in a:
            pump.click()
            
        if "6" in a:
            for n in range(20):
                n+=1
                pwm = 255
                duration = 20
                #s = "hello\n"
                s = f"pump,{int(pwm)},{int(duration)}\n"
                pump.send( s )
                print( s, n  )
                #pump.pump( 255, 20 )
                sleep(0.1)
                s = f"flush,255,100\n"
                pump.send( s )
                print( s, n  )
                sleep(0.1)
        if "7" in a:
            
            pump.click()
            sleep(0.1)
            pump.deliverDrop( 1 )
            pump.lightOn(255) 
            
        if "8" in a:
            for n in range(10):
                print("dropping --")
                pump.deliverDrop( 1 )
                sleep(0.3)
        
        if "9" in a:
            
            print("big drop")
            pump.deliverDrop( 10 )
            sleep(0.3)
            

            
            
    
    '''
    n= 1
    while True:
        n+=1
        pwm = 255
        duration = 20
        #s = "hello\n"
        s = f"flush,{int(pwm)},{int(duration)}\n"
        pump.send( s )
        print( s, n  )
        #pump.pump( 255, 20 )
        sleep(0.1)
    ''' 
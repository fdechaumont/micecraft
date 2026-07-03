'''
Created on 26 sept. 2025

@author: Fab
'''
import logging
import sys
from micecraft.devices.gate.Gate import Gate, GateOrder

if __name__ == '__main__':
    
    #logging.basicConfig(level=logging.INFO, filename="test.txt", format='%(asctime)s.%(msecs)03d: %(message)s', datefmt='%Y-%m-%d %H:%M:%S' )
    #logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    
    gate = Gate( COM_Servo="COM6", COM_Arduino="COM4", COM_RFID="COM3" )
    print( "test")
    #gate.setOrder( GateOrder.ONLY_ONE_ANIMAL_IN_B )
    gate.doorA.open()
    gate.doorB.close()
    input("Hit enter to stop example")
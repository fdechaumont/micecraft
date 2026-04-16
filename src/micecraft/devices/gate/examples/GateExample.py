'''
Created on 26 sept. 2025

@author: Fab
'''
from micecraft.devices.gate.Gate import Gate, GateOrder

if __name__ == '__main__':
    
    gate = Gate( COM_Servo="COM12", COM_Arduino="COM13", COM_RFID="COM14" )
    gate.setOrder( GateOrder.ONLY_ONE_ANIMAL_IN_A )
    input("Hit enter to stop example")
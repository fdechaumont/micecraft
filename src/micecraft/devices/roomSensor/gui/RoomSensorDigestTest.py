'''
Created on 27 mars 2024

@author: Fab
'''
#from blocks.sensors.roomsensor.RoomSensorDigest import RoomSensorDigest
from micecraft.devices.roomSensor.RoomSensorDigest import RoomSensorDigest

#from blocks.sensors.roomsensor.RoomSensorDigest import RoomSensorDigest

if __name__ == '__main__':
    
    def listener( event ):
        
        print("-------- data from sensor:")
        print( event.description )        
        
        
    roomSensorDigest = RoomSensorDigest( comPort="COM12" , delayS=10 )
    roomSensorDigest.addDeviceListener( listener )    
    roomSensorDigest.roomSensor.setDelaySampling( 200 , 20 )
    
        
    input("hit enter to stop")
    roomSensorDigest.shutdown()
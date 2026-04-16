'''
Created on 22 sept. 2025

@author: Fab
'''
from micecraft.devices.lever.Lever import Lever

if __name__ == '__main__':

    def myListener( event ):
        print( f"Event received:  {event}"  )
    
    lever = Lever( "COM24", "myLever" )
    lever.addDeviceListener( myListener )
    
    input("Press enter to stop the test")
    lever.shutdown()
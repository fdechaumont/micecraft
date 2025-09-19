'''
Created on 7 juin 2022

@author: Fabrice de Chaumont
'''
from datetime import datetime

class DeviceEvent(object):
    '''
        Example:        
            DeviceEvent( "gate", gate, "animal in A", myData )
    '''
    def __init__(self, deviceType : str , deviceObject : object , description : str , data=None ):
        
        self.deviceType = deviceType
        self.deviceObject = deviceObject
        self.description = description
        
        self.data = data
        self.datetime = datetime.now()
                
    def __str__(self):
        s = "DeviceEvent *" + str(self.deviceType) +"*"+ str( type( self.deviceObject) ) + "*no name*" + str( self.description ) 
        try:
            s = "DeviceEvent *" + str(self.deviceType) +"*"+ str( type( self.deviceObject) ) + "*" + str( self.deviceObject.name ) + "*" + str( self.description )
            s = "DeviceEvent *"+ str ( self.deviceType ) +"*"+ str( type( self.deviceObject) ) + "*" + str( self.deviceObject.name) + "*" + str( self.description ) + "*" + str( self.data )
        except:
            pass
        return s
    


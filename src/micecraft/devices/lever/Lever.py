'''
Created on 30 mars 2023

@author: Fab
'''




from datetime import datetime

import logging
from micecraft.soft.ComManager.ComManager import ComManager
from micecraft.soft.DeviceEvent.DeviceEvent import DeviceEvent


class Lever(object):

    def __init__(self, comPort = "COM24" , name="Lever" , debounceDurationS=1 ):
        
        self.name = name
        self.comPort = comPort
        self.serialPort = None
        
        # instantiate the ComManager to send/receive commands to/from the arduino
        self.comManager = ComManager( comPort, self.comListener, alarmName = "Lever" )
        
        # the list of devices registered to get messages from the lever
        self.deviceListenerList =[]
        self.enabled = True
                
        self._lightOn = False
        
        self.lastDownTime = datetime.now()
        self.debounceDurationS = None
        self.setDebounceDurationS(debounceDurationS)
    
    def setDebounceDurationS(self , debounceDurationS ):
        if self.debounceDurationS != debounceDurationS:
            self.debounceDurationS = debounceDurationS
            logging.info(f"Lever {self.comPort}: DebounceDuration set to {self.debounceDurationS} s")
    
    def shutdown(self):
        self.enabled = False
        self.comManager.stop()
        
    
    def comListener(self , event ):
                        
        if event.description == "release":
            self.release()
                        
        if event.description == "press":
            self.press()
    
    
    def release(self):
        self.fireEvent( DeviceEvent( "Lever", self, "lever release", data="release" ) )
            
    def press(self):
        durationS = ( datetime.now() - self.lastDownTime ).total_seconds()
        if durationS > self.debounceDurationS:                  
            self.fireEvent( DeviceEvent( "Lever", self, "lever press", data="press" ) )
            self.lastDownTime = datetime.now()
        else:
            # this event should not be processed by the listener, it is just to provide an info that the animal smashed the lever again.
            # that might also be a flicker in the reading of the sensor.
            # the event does not contain "press" in its description to avoid problem if a user matches the string with "press". In that case one would have the debounced events too.
            self.fireEvent( DeviceEvent( "Lever", self, f"lever debounced - duration until last hit: {durationS}" ) )
        
        
    def click(self ):
        
        self.send( "click")
        self.fireEvent( DeviceEvent( "Lever", self, "click" ) )

    def lightOn(self ):
        self.light( True )
        
    def lightOff(self ):
        self.light( False )
            
    def light(self , on, pinNumber=11, pwm=255 ):
        if on:
            order = f"lightOn {pinNumber},{pwm}"
            self.log( order )
            self.send( order )
            self.fireEvent( DeviceEvent( "Lever", self, "lightOn" ) )
            self._lightOn = True
        else:
            order = f"lightOff {pinNumber}"
            self.log( order )
            self.send( order )
            self.fireEvent( DeviceEvent( "Lever", self, "lightOff" ) )
            self._lightOn = False
            
    def isLightOn(self ):
        return self._lightOn
    
    def switchLight(self):
        if self._lightOn:
            self.light( False )
        else:
            self.light( True )
        
    def send(self, message ):
        
        if self.comManager.send(message) == False:
            self.log( f"Can't send message to device: {message}" )
        
        '''
        message+="\n"
        #print( "sending... " , message )
                        
        try:
            self.serialPort.write( message.encode("utf-8") )        
        except serial.SerialException as e:
            self.log( "Critical error: serial disconnected")
            self.alarmConnect.sendAlarmMail( AlarmState.ALARM_ON , "Lever disconnected." )                
            try:
                self.connect()
                self.log( "reconnect ok" )
                self.alarmConnect.sendAlarmMail( AlarmState.ALARM_OFF , "re-Connected." )
            except:
                self.log( "Can't reconnect" )
            sleep( 1 )
        '''
            
    def isAlarmOn(self):
        
        if not self.comManager.isConnected():
            return "Device disconnected"
        
        return False    
            
    def log(self, message ): 
        print( f"Lever: {self.name} {self.comPort} {message}" )       
        logging.info( f"Lever: {self.name} {self.comPort} {message}")
    
    def fireEvent(self, deviceEvent ):
        for listener in self.deviceListenerList:
            listener( deviceEvent )
    
    def addDeviceListener(self , listener ):
        self.deviceListenerList.append( listener )
        
    def removeDeviceListener(self , listener ):
        self.deviceListenerList.remove( listener )
        
    def __str__(self, *args, **kwargs):
        return self.name + " " + self.comPort
    
    
    
    
    
    
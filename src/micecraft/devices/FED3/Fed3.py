'''
Created on 10 mars 2022

@author: Fab
'''


import threading
from time import sleep
from datetime import datetime
from random import randint
import logging

from micecraft.soft.alarm.Alarm import AlarmState, Alarm
from micecraft.soft.device_event.DeviceEvent import DeviceEvent
from micecraft.soft.com_manager.ComManager import ComManager


class Fed3(object):

    
    def __init__(self, comPort = "COM79" , name="Fed3"):
        
        self.name = name
        self.comPort = comPort 
        
        self.comManager = ComManager( comPort, self.comListener, alarmName = "Fed3" )
        
        self.lock = threading.Lock()
    
        self.nbRight = 0
        self.nbLeft = 0
        
        self.capacityMG = 12000
        self.refillPelletLevel()
        
        self.deviceListenerList =[]
        self.enabled = True
                
        self.lastPelletDeliveredTime = datetime.now() # if a pellet is already available in the fed at startup, this value will be used to provide the time the animal took to pick the pellet        
        self._pelletWaitingForPickup = False
        self._pelletPresent = False
        self._lastPingTime = datetime.now()

        self.lastFeedOrderDateTime = None
        self._feeding = False
        self.timeOutFeedSeconds = 10 # maximum time to get a pellet
        
        self.alarmPellet = Alarm( f"Deliver Pellet - Fed Manager:{self.name}" )
        self.alarmConnect = Alarm( f"Connection - Fed Manager:{self.name}" )
        
        self.feedCheckThread = threading.Thread(target=self.feedCheckLoop , name = f"FED feed check thread - {self.comPort}")
        self.feedCheckThread.start()
        
        self.hello()        
    
    
    def unJamFeeder(self):
        value = randint( -30,30 )
        self.send(f"rotation:{value}")
    
    def setCapacityInMG( self, capacityMG ):
        self.capacityMG = capacityMG
        
    def setPelletLevelInMG( self, pelletLevel ):
        self.pelletLevel = pelletLevel

    def refillPelletLevel( self ):
        self.pelletLevel = self.capacityMG
        
    def getCapacityMG(self):
        return self.capacityMG
    
    def getLiquidLevelML(self):
        return self.liquidLevel
        
    def stop(self):
        self.enabled = False
        
    def shutdown(self):
        self.comManager.shutdown()
        self.stop()
        
    def rightIn(self):
        self.nbRight+=1
        self.fireEvent( DeviceEvent( "fed3", self, "nose poke right", data="right" ) )
         
    def leftIn(self):
        self.nbLeft+=1
        self.fireEvent( DeviceEvent( "fed3", self, "nose poke left", data="left" ) )
       
       
    def comListener(self , event ):
        
        
        self.log( event.description )
        
        if "rightIn" in event.description:
            self.rightIn()
            
        if "leftIn" in event.description:
            self.leftIn()
            
        if "hello" in event.description:
            self.fireEvent( DeviceEvent( "fed3", self, event.description ) )
                    
        if  "already _feeding" in event.description: # the fed received a feed oder as it is already trying to deliver a pellet
            self.fireEvent( DeviceEvent( "fed3", self, "already _feeding" ) )
            
        if "pellet already delivered" in event.description: # the fed received a feed order but a pellet is already available in the distributor for the animal 
            self._feeding = False
            self._pelletWaitingForPickup = True
            self.fireEvent( DeviceEvent( "fed3", self, "pellet already delivered" ) )
            
        if "pellet delivered" in event.description:
            self._feeding = False
            self.lastPelletDeliveredTime = datetime.now()                    
            self._pelletWaitingForPickup = True
            self.pelletLevel-=20
            
            deltaS = 0
            try:
                delta = datetime.now()-self.lastFeedOrderDateTime
                deltaS = delta.total_seconds()
            except:
                print("fed 3 manager error: can't convert (1)")                    
            
            self.fireEvent( DeviceEvent( "fed3", self, f"pellet delivered in {deltaS} seconds", deltaS ) )
            self.alarmPellet.sendAlarmMail( AlarmState.ALARM_OFF , "Pellet delivered." )
                        
        if "pellet picked" in event.description:
            self._pelletWaitingForPickup = False
            
            deltaS = 0
            try:
                delta = datetime.now()-self.lastPelletDeliveredTime
                deltaS = delta.total_seconds()
            except:
                print("fed 3 manager error: can't convert (2)")                    

            self.fireEvent( DeviceEvent( "fed3", self, f"pellet picked after {deltaS} seconds" , deltaS ) )
            
        if "pellet present" in event.description:
            self._pelletPresent = True
            self.fireEvent( DeviceEvent( "fed3", self, "pellet present" ) )
        
        if "pellet not present" in event.description:
            self._pelletPresent = False
            self.fireEvent( DeviceEvent( "fed3", self, "pellet not present" ) )
            
        if "motor step set to" in event.description:
            self.fireEvent( DeviceEvent( "fed3", self, event.description ) )
            
    
    def feedCheckLoop(self):
        
        # check feed timeout            
        while( self.enabled ):
            sleep( 0.1 )
            if self._feeding:
                if self.lastFeedOrderDateTime!=None:
                    delta = datetime.now()-self.lastFeedOrderDateTime
                                        
                    if delta.total_seconds() > self.timeOutFeedSeconds:
                        print("Fed 3 _feeding Timeout... canceling _feeding...")
                        self.alarmPellet.sendAlarmMail( AlarmState.ALARM_ON , "Can't provide pellet." )
                        self.cancelFeed()
                    
                    if self._feeding and delta.total_seconds() > self.timeOutFeedSeconds/2:                        
                        self.unJamFeeder()
            
    def log(self, message ):        
        logging.info( f"FED3: {self.name} {self.comPort} {message}")

    def hello(self):
        self.send("hello")
        

    def getNumberOfSecondSincePelletIsAvailableToAnimal(self):
        # return the number of second since the last pellet delivered is available to animal
        
        if self._pelletWaitingForPickup == True:
            delta = datetime.now()-self.lastPelletDeliveredTime
            return delta.total_seconds()
        
        return None
            
    def isFeeding(self):
        return self._feeding
    
    def isPelletWaitingForPickup(self):
        # This events is true if a feed order has been given and the pellet has not been picked by the animal yet
        # if the animal pick the pellet and drop it again in the fed, this will be considered as picked up. Check isPelletPresent() otherwise.        
        return self._pelletWaitingForPickup
    
    def isPelletPresent(self):
        # this provides if the pellet is present, whatever the feeding state is.
        return self._pelletPresent
    
    def cancelFeed(self):
        self._feeding = False
        self.send( "cancel feed")
        self.fireEvent( DeviceEvent( "fed3", self, "cancel feed" ) )
        
    def feed(self):
        self.lastFeedOrderDateTime = datetime.now()
        self._feeding = True
        self.send( "feed")
        self.fireEvent( DeviceEvent( "fed3", self, "feed" ) )
    
    def setMotorStep(self , value ):
        value = int( value )
        self.fireEvent( DeviceEvent( "fed3", self, f"sending motor step speed order: {value}" ) )
        self.send( f"step:{value}" )
    
    def click(self):
        self.send( "click")
        self.fireEvent( DeviceEvent( "fed3", self, "click" ) )
    
        
    def light( self, r, g, b, w, side ):
        
        # r,g,b,w: 0 to 255
        # side: l: left hole, r: right hole, b: left and right holes, c: apply to all leds in center of device, cl: center left led, cr: center right, a: all leds
        # command example: RGBWdef_R000_G100_B100_W100_Sidel
        def checkValue( *vals ):
            for val in vals:
                #print( val )
                if not( val >= 0 and val <=255 ):
                    return False
            return True
                    
        if not checkValue( r,g,b,w ):
            logging.info(f"Error in fed command for fed named *{self.name}* values received were: {r} {g} {b} {w}")
        
        side =side.lower()        
        command = f"RGBWdef_R{r}_G{g}_B{b}_W{w}_Side{side}"
        self.send( command )
        
            
    def lightoff(self):
        self.send( "lightoff")
        self.fireEvent( DeviceEvent( "fed3", self, "lightoff" ) )
    
    def send(self, message ):
        
        self.comManager.send(message)
        
    def fireEvent(self, deviceEvent ):
        print(f"fire event {deviceEvent}")
        for listener in self.deviceListenerList:
            listener( deviceEvent )
    
    def addDeviceListener(self , listener ):
        self.deviceListenerList.append( listener )
        
    def removeDeviceListener(self , listener ):
        self.deviceListenerList.remove( listener )
        
    def __str__(self, *args, **kwargs):
        return self.name+ ": nbLeft: " + str( self.nbLeft ) + " nbRight: " + str ( self.nbRight )
    
    
    
    
    
    
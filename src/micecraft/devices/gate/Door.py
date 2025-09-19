'''
Created on 23 sept. 2021

@author: Fab
'''
import numpy as np
from enum import Enum
import time
import logging
from micecraft.devices.gate.Parameters import *
from micecraft.soft.device_event.DeviceEvent import DeviceEvent


class DoorStatus(Enum):
    OPENED = 0 # door is opened
    OPENING = 1 # is trying to open the door
    CLOSED = 2 # door is closed
    CLOSING = 3 # is trying to close the door
    JAMMED_OPEN = 4 # an error prevented the door from opening/closing
    JAMMED_CLOSE = 5 # an error prevented the door from opening/closing
    UNKOWN = 6
    CHECKING_CLOSE_LIDAR = 7
    
class DoorOrder(Enum):
    OPEN = 1
    CLOSE = 2
    NO_ORDER = 3

class Door(object):
    '''
    Manage a door
    '''
    
    
    def __init__(self, motor , name , lidarEnabled ):  # TODO: lock should not be used anymore here
        '''
        Constructor
        '''
        self.deviceListenerList = []
        self.motor = motor
        self.torqueLimit = DEFAULT_TORQUE_AND_SPEED_LIMIT_MOUSE # 1023 max
        self.speedLimit = DEFAULT_TORQUE_AND_SPEED_LIMIT_MOUSE  # 1023 max
        self.positionTolerance = 10
        self.name= name
        self.status = DoorStatus.UNKOWN            
        #self.lock= lock
        self.previousPosition = None
        self.doorOrder = DoorOrder.NO_ORDER
        self.cacheOpenPercentage = 50
        self.setLimits( OPENED_DOOR_POSITION_MOUSE, CLOSED_DOOR_POSITION_MOUSE )
        self.getClosePercentage()
        self.jamDelay = 0
        self.jamCheck = True
        self.closingLidarCheck = 0 # number of call to performLogic to test if lidar is okay to close the door
        self.lidarIn = False
        self.lidarExt= False
        self.lidarEnabled = lidarEnabled
        
        self.securityLevel = 2
        
        ''' 
        by default, the motor torque is de-activated when the door reach the close position. (this is to avoid potential buzzing sound of motors that may annoyed the animals)
        Then if an animal tries to open the door, the door re-activate and re-close.
        The opening of the door is check eached 250ms.
        In rat mode, the torque should be kept with the flag self.keepTorqueActiveWhileDoorAreClosed because they are too strong and may open the door if no torque is applied on the motor.
        '''
        self.keepTorqueActiveWhileDoorAreClosed = False 
        
    '''
    def setJammed(self ):
        print("Door JAMMED " )        
        #ms = int( time.time()*1000.0 )
        #self.previousJamTime = ms
        #print ("Address in jamm set : ", hex(id(self.previousJam)) )
        #print( "previous jam time: " , self.previousJamTime )
        self.jamDelay=2
        self.status = DoorStatus.JAMMED
        print("DOOR JAMMED DONE")        
    ''' 
        
    '''
    def setStatus(self, status ):
        self.status = status
        self.fireEvent( DeviceEvent( "Door", self, f"Status changed:{self.status}", self.status ) )
    '''
    
        
    def fireEvent(self, deviceEvent ):
        for listener in self.deviceListenerList:
            listener( deviceEvent )
            
    def addDeviceListener(self , listener ):
        self.deviceListenerList.append( listener )
        
    def removeDeviceListener(self , listener ):
        self.deviceListenerList.remove( listener )    
    
    def log(self, message ):
        message="[door " + self.name + "] " + str(message)
        logging.info( message )
        self.fireEvent( DeviceEvent( "Door", self, message ) )
    
    def setJamCheck(self, enable ): # jamCheck can be disabled and will be put back on next time the door is closed.
        if self.jamCheck != enable:
            self.log( "JamCheck changed: " + str(enable) )
        self.jamCheck = enable
        
    def getLidarIn(self):
        return self.lidarIn
    
    def getLidarExt(self):
        return self.lidarExt
    
    def isLidarEnabled(self):
        return self.lidarEnabled
    
    def performLogic(self):
        
        #cm = CodeMonitoring( self.name )
        
        closePercentage = self.getClosePercentage()
        #cm.read( "step 01")
        
        self.jamDelay -=1 
        if self.jamDelay < 0:
            self.jamDelay = 0
        if self.jamDelay !=0:
                  
            #print("DOOR JAM CANCEL")
            if self.status==DoorStatus.JAMMED_OPEN:
                #print( "close")
                self.setMotorPosition( self.closePosition )
            if self.status==DoorStatus.JAMMED_CLOSE:
                #print( "open")
                self.setMotorPosition( self.openPosition )
            return
        #cm.read( "step 02")
        #self.lock.acquire()
        p = int ( self.motor.get_position( ) )
        #self.lock.release()
        #cm.read( "step 03")
        
        # other logic            
        
        if self.status == DoorStatus.JAMMED_OPEN or self.status == DoorStatus.JAMMED_CLOSE:
            self.log( "JAMMED - Restart order: " + str( self.doorOrder ) )
            #print("restart order / current pos = " , p )
            if self.doorOrder == DoorOrder.OPEN:
                self.previousPosition = None
                self.open()
                #cm.read( "step 04")
                return
            
            if self.doorOrder == DoorOrder.CLOSE:
                self.previousPosition = None
                self.close()
                #cm.read( "step 05")    
                return
        
        if self.status == DoorStatus.OPENING:
            if self.isOpenedPositionReached():
                self.log( "OPENED" )
                self.status= DoorStatus.OPENED
                self.setTorqueEnabled(False)
                self.previousPosition = p
                #cm.read( "step 06")
                return
                #print("Door ", self.name, " OPENED")
                
        if self.status == DoorStatus.CLOSING:
            if self.isClosedPositionReached():
                self.status = DoorStatus.CHECKING_CLOSE_LIDAR
                self.closingLidarCheck= DURATION_OF_LIDAR_CLOSE_TEST
                                
        if self.status == DoorStatus.CHECKING_CLOSE_LIDAR:
            self.closingLidarCheck=self.closingLidarCheck-1
            #print( "closing lidar check step: " , self.closingLidarCheck )
            if self.isLidarEnabled():
                #if self.lidarExt and self.lidarIn: # not enough security
                if self.lidarIn:
                    # switch back the door in jam mode
                    self.jamDelay = 3
                    self.status = DoorStatus.JAMMED_CLOSE
                    self.log( str( self.status ) + " reason: LIDAR")
                    self.setMotorPosition( self.openPosition )
                    self.previousPosition = p
                    #cm.read( "step 07")
                    return
                            
            if self.closingLidarCheck<0 or not self.isLidarEnabled():
                self.log( "CLOSED" )
                self.status= DoorStatus.CLOSED
                self.setJamCheck( True )
                
                if self.keepTorqueActiveWhileDoorAreClosed:
                    self.setTorqueEnabled(True)
                else:                    
                    self.setTorqueEnabled(False)
                
                #self.setTorqueEnabled(False)
                self.previousPosition = p
                #cm.read( "step 08")
                return
            
        if self.status == DoorStatus.OPENING:
            if p == self.previousPosition: # jammed                                                
                self.jamDelay=3
                if self.jamCheck:
                    self.status = DoorStatus.JAMMED_OPEN
                    self.log( self.status )
                    self.setMotorPosition( self.closePosition )
                    self.previousPosition = p
                    #cm.read( "step 09")
                    return                

        if self.status == DoorStatus.CLOSING:
            if self.jamCheck:
                if closePercentage>0:
                    if self.isLidarEnabled():
                                                                        
                        if self.securityLevel == 2:
                            lidarTest = self.lidarExt and self.lidarIn
                        
                        if self.securityLevel == 3:
                            lidarTest = self.lidarExt or self.lidarIn
                            
                        # LIDAR safety
                        #if self.lidarExt and self.lidarIn: # or : max security
                        if lidarTest:
                            self.jamDelay = 3
                            self.status = DoorStatus.JAMMED_CLOSE
                            self.log( str( self.status ) + "reason: LIDAR")
                            self.setMotorPosition( self.openPosition )
                            self.previousPosition = p
                    
            
            #self.log( f" motor current position: {p} previous position: {self.previousPosition}" )
            if p == self.previousPosition: # jammed
                #print("Door jammed / position = " , p , "closing position is: " , self.closePosition , "Jam delay: " , self.jamDelay )                
                self.jamDelay=3
                if self.jamCheck:
                    self.status = DoorStatus.JAMMED_CLOSE
                    self.log( self.status )
                    self.setMotorPosition( self.openPosition )
                    self.previousPosition = p
                    #cm.read( "step 10")
                    return
        
        # watch if animals try to re-open the door
        if self.doorOrder == DoorOrder.CLOSE and self.status==DoorStatus.CLOSED:
            if closePercentage < RE_CLOSING_THRESHOLD_PERCENTAGE:
                self.log( "Door watch: re-closing door" )
                #print("Door watch: re-closing door")
                self.setJamCheck( False )
                self.close( force=True )
                self.previousPosition = p
                #cm.read( "step 11")
                return
                
        self.previousPosition = p
        
        #cm.read( "step end")
        

    def setMotorPosition(self , position ):
        
        #self.lock.acquire()
        self.motor.set_position( position )
        #self.lock.release()
        
    def setTorqueEnabled(self, enabled ):
        
        #self.lock.acquire()
        if enabled:
            self.motor.enable_torque()            
        else:
            self.motor.disable_torque()            
        #self.lock.release()
    
    def safeMode(self):
        self.torqueLimit = 100
        self.speedLimit = 100
        
    def setLimits(self , openPosition, closePosition ):
        self.openPosition = openPosition
        self.closePosition = closePosition        
    
    def setSpeedAndTorqueLimits(self, speedLimit , torqueLimit ):
        self.speedLimit = speedLimit
        self.torqueLimit = torqueLimit
        self.setMotor()
    
    def setMotor(self):
        #self.lock.acquire()
        self.motor.set_moving_speed( self.speedLimit )
        self.motor.set_torque_limit( self.torqueLimit )
        
        #self.lock.release()
            
    def open(self):
        #print( "OPEN DOOR")
        self.log( "OPEN" )
        self.doorOrder = DoorOrder.OPEN
        self.setMotor()    
        self.status = DoorStatus.OPENING
        self.setTorqueEnabled(True)
        self.setMotorPosition( self.openPosition )        
        
    def close(self , force = False):
        self.log( "CLOSE" )
        
        if not force:
            if self.status == DoorStatus.CLOSED:
                self.log("receive close: Door already closed")
                return
        
        self.log("Forcing close")
        self.doorOrder = DoorOrder.CLOSE
        self.setMotor()            
        self.status = DoorStatus.CLOSING
        self.setTorqueEnabled(True)
        self.setMotorPosition( self.closePosition )
        
    def calibrate(self):
        print("Calibrate ", self.name )
        self.doorOrder = None
        #self.lock.acquire() # open
        print("Calibrate Step1 ", self.name )        
        self.motor.set_moving_speed( 100 )
        self.motor.set_torque_limit( 100 )
        self.motor.set_position( self.openPosition )
        #self.lock.release()
        time.sleep(3)
        #self.lock.acquire() # try to close
        print("Calibrate Step2 ", self.name )
        self.motor.set_moving_speed( 100 )
        self.motor.set_torque_limit( 100 )
        self.motor.set_position( 1000 )
        #self.lock.release()
        time.sleep(3)
        #self.lock.acquire()
        p = self.motor.get_position( )
        p = p - 10
        #self.lock.release()
        self.setLimits( p-200, p )
        print("Calibration done : open:", self.openPosition, "close: ", self.closePosition , self.name )
        
        
    def isClosedPositionReached(self):
        if self.getClosePercentage() > OPEN_CLOSE_SENSITIVITY_PERCENTAGE:        
            return True
        return False
        
    def isOpenedPositionReached(self):
        if self.getOpenPercentage() > OPEN_CLOSE_SENSITIVITY_PERCENTAGE:        
            return True
        return False
    
    def getClosePercentage(self):
        #self.lock.acquire()
        try:
            p = self.motor.get_position( )
        except Exception as e:
            logging.info("CRITICAL ERROR In motor control")
            p = int ( ( self.openPosition + self.closePosition ) / 2 ) # set position to intermediate to tell the system no final position is reached.
            logging.info ( e )
        #self.lock.release()
        
        #print( self.openPosition , self.closePosition )
        
        xp = [ min( self.openPosition , self.closePosition ) , max( self.openPosition , self.closePosition ) ]
        fp = [ 0, 100 ]
        closePercent = np.interp( p, xp, fp)        
        self.cacheOpenPercentage = 100-closePercent 
        return np.interp( p, xp, fp)
        
        
    def getOpenPercentage(self):
        return 100-self.getClosePercentage()
        
    def isOrderDone(self):
        if self.doorOrder == DoorOrder.CLOSE:
            return ( self.status == DoorStatus.CLOSED )
        if self.doorOrder == DoorOrder.OPEN:
            return ( self.status == DoorStatus.OPENED )
        
        
        
        
        
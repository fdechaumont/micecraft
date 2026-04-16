'''
Created on 16 mars 2022

@author: Fab
'''

import serial
from time import sleep
import logging
import threading
from micecraft.soft.alarm.Alarm import Alarm
from micecraft.soft.com_manager.ComManager import ComManager
from micecraft.soft.device_event.DeviceEvent import DeviceEvent


class WaterPump(object):

    
    def __init__(self, comPort = "COM90" , name="WaterPump" ):
        
        self.name = name
        self.comPort = comPort 
        logging.info(f" {self.name} {self.comPort}: Waterpump init...")

        #self.serialPort = serial.Serial( port=comPort, baudrate=115200, bytesize=8, timeout=50 )        

        self.alarmConnect = Alarm( f"Connection - Water pump :{self.name}" )
        
        
        self.nbDrop = 0
        self.deviceListenerList = []
        
        self.capacityML = 10
        self.liquidLevel = self.capacityML
        
        self.oneDropDuration = 17
        self.oneDropPWM = 255
        self.oneDropML = 0.1
        self.enabled= True
        
        self.rewardDelivered = False
        self.rewardPicked = False
        
        self._lightOn = False
        
        '''
        self.readThread = threading.Thread(target=self.read , name = f"Pump Thread - {self.comPort}")
        self.readThread.start()
        '''
        
        
        #sleep( 2 ) # init of transmission
        self.comManager = ComManager( self.comPort, self.comListener, alarmName = "WaterPump" ) #, baudrate=9600 )
        logging.info("Waterpump ready")
    
    '''
    def connect(self):
        try:
            self.serialPort.close()
        except:
            # serial already close or object not initialized
            pass
        
        #self.serialPort = serial.Serial( port=self.comPort, baudrate=115200, bytesize=8, timeout=50 )
        try:
            self.serialPort = serial.Serial( port=self.comPort, baudrate=115200, bytesize=8, timeout=SERIAL_READ_TIMEOUT, write_timeout=SERIAL_WRITE_TIMEOUT )
        except:
            self.log("Fail at reconnect (this is a temp fix before the next communication layer takes over)")
    '''
        
    
    def isAlarmOn(self):
        
        if not self.comManager.isConnected():
            return "Device disconnected"
        
        return False
    
    def shutdown(self):
        self.enabled = False
        self.comManager.shutdown()
                
    
    def setDropParameters(self , pwm, duration, ml ):
        
        self.oneDropPWM = pwm
        self.oneDropDuration = duration
        self.oneDropML = ml
    
    def _rewardPicked(self):
        self.rewardPicked = True
        self.fireEvent( DeviceEvent("waterpump", self, "reward picked", None ) )
        # question: should the self.rewardDelivered be set to False or not ?

    
    def comListener(self , event ):
        
        if "animal in" in event.description:
            self.fireEvent( DeviceEvent("waterpump", self, "animal in", None ) )
            if self.rewardDelivered and not self.rewardPicked:
                self._rewardPicked()

        if "animal out" in event.description:
            self.fireEvent( DeviceEvent("waterpump", self, "animal out", None ) )
        
    
    '''
    def read(self):
        
        while( self.enabled ):
            
            try:
                
                if self.serialPort.in_waiting > 0:
                                        
                    #serialString = self.serialPort.readline().decode("Ascii")
                    
                    serialString = ""
                    line = self.serialPort.readline()
                    try:
                        serialString = line.decode("utf-8")
                    except Exception as e:                        
                        self.log(f"Error in utf-8 decode {e}")
                        
                    serialString = serialString.strip()
                    self.log(f"received: {serialString}")
                    #print( "serial string: " , serialString )
                    
                    if "animal in" in serialString:
                        self.fireEvent( DeviceEvent("waterpump", self, "animal in", None ) )
                        if self.rewardDelivered and not self.rewardPicked:
                            self.rewardPicked = True
                            self.fireEvent( DeviceEvent("waterpump", self, "reward picked", None ) )
                            # question: should the self.rewardDelivered be set to False or not ?
    
                    if "animal out" in serialString:
                        self.fireEvent( DeviceEvent("waterpump", self, "animal out", None ) )
                    
                    
            
            except serial.SerialException:
                self.log("Error in serial. Disconnected ?")
                self.serialPort.close()                
                
                self.connect()
                #print("test")
                sleep( 1 )
                
            sleep( 0.005 )
                         
        self.serialPort.close()   
    '''
            
    def setCapacityInML( self, capacityML ):
        self.capacityML = capacityML
        
    def setLiquidLevel( self, liquidLevel ):
        self.liquidLevel = liquidLevel

    def refillLiquidLevel( self ):
        self.liquidLevel = self.capacityML
        self.fireEvent( DeviceEvent( "waterpump", self, f"refilled - remaining: {self.getLiquidLevelML()}  ml" ) )
        
    def getCapacityML(self):
        return self.capacityML
    
    def getLiquidLevelML(self):
        return self.liquidLevel

    def prime( self ):
        self.deliverDrop( 60 )
        
    def _rewardDelivered(self):
        self.rewardDelivered = True
        self.rewardPicked = False
            
    def deliverDrop(self , numberOfDrop=1 ):
        s = f"pump drop(s) delivered: {numberOfDrop} - remaining: {self.getLiquidLevelML()}  ml"
        self.fireEvent( DeviceEvent( "waterpump", self, s ) )        
        self.pump( self.oneDropPWM, self.oneDropDuration*numberOfDrop )
        self.liquidLevel -= self.oneDropML
        self._rewardDelivered()            
    
    def pump( self, pwm, duration, ml=0.1 ):
        s = f"pump,{int(pwm)},{int(duration)}"
        self.send( s )
        self.fireEvent( DeviceEvent( "waterpump", self, s ) )
        self._rewardDelivered()
        print( s )
        
    def flush( self, pwm=255, duration=500 ):
        s = f"flush,{int(pwm)},{int(duration)}"
        self.send( s )
        self.fireEvent( DeviceEvent( "waterpump", self, s ) )
        print( s )
        self.rewardDelivered = False
        self.rewardPicked = False

        
    def lightOn( self, pwm=255 ):
        s = f"lightOn,{int(pwm)}"
        self.send( s )
        self._lightOn = True
        self.fireEvent( DeviceEvent( "waterpump", self, s ) )
        print( s )
        
    def lightOff( self ):
        s = f"lightOff"
        self.send( s )
        self._lightOn = False
        self.fireEvent( DeviceEvent( "waterpump", self, s ) )
        print( s )

    def isLightOn(self):
        return self._lightOn

    def setClickFrequency( self, frequency ): # fixme: the call should be frequency,frequency instead of ":"
        s = f"frequency:{int(frequency)}"
        self.send( s )
        self.fireEvent( DeviceEvent( "waterpump", self, s ) )
        print( s )

    def click( self ):
        s = f"click"
        self.send( s )
        self.fireEvent( DeviceEvent( "waterpump", self, s ) )
        print( s )
        
    
    '''
    def drop(self):
        self.send( "drop")
        self.fireEvent( DeviceEvent( "waterpump", self, "drop" ) )
        print( "drop")
    
    def primePump(self):
        self.send( "prime")
        self.fireEvent( DeviceEvent( "waterpump", self, "prime pump" ) )
        print("prime pump")
    '''
    
    
    def send(self, message ):
        
        self.comManager.send(message)
        
    '''
    def send(self, message ):
        
        message+="\n"
        try:
            self.serialPort.write( message.encode("utf-8") )
            
        except serial.SerialException as e:
            self.log( "Critical error: serial disconnected")
            self.alarmConnect.sendAlarmMail( AlarmState.ALARM_ON , "Water pump disconnected." )                
            try:
                self.connect()
                self.log( "reconnect ok" )
                self.alarmConnect.sendAlarmMail( AlarmState.ALARM_OFF , "water pump re-Connected." )
            except:
                self.log( "Can't reconnect" )
                
    ''' 
        
    def __str__(self, *args, **kwargs):
        return "Water pump: " + self.name + " nb drop : " + str( self.nbDrop )

    def fireEvent(self, deviceEvent ):
        for listener in self.deviceListenerList:
            listener( deviceEvent )
    
    def addDeviceListener(self , listener ):
        self.deviceListenerList.append( listener )
        
    def removeDeviceListener(self , listener ):
        self.deviceListenerList.remove( listener )
        
    def log(self, message ):        
        logging.info( f"WaterPump: {self.name} {self.comPort} {message}")

'''
Created on 6 dec. 2024

@author: Fabrice de Chaumont
'''

import serial
import threading
from time import sleep

import logging

import atexit
from serial.serialutil import SerialException
from datetime import datetime, timedelta
from micecraft.soft.alarm.Alarm import Alarm, AlarmState
from micecraft.soft.DeviceEvent.DeviceEvent import DeviceEvent

class ComManager(object):
    
    '''    
    Communication manager via COM port with the following features:
     
    connect/reconnect and error handling 
    auto release resources on exit with atexit (done)
    auto check device speed (done)
    alarm handling (done)
    ping mode ( done )
    
    Restrictions:
    - String received should all finish by a \n, so that the system knows that a message is complete.
    - String sent d have a \n added to their end, so that the receiver on the other side can use it.
    '''


    def __init__(self, comPort : str, deviceListener, alarmName="", baudrate = 115200 , listener_kwargs={}):
        
        self.comPort = comPort
        self.baudrate = baudrate
        self.readBuffer = "" # contains incomplete messages
        self.connected = False
                
        
        atexit.register(self.stop)
        self.deviceListenerList = []
        self.addDeviceListener( deviceListener, listener_kwargs )
        self.enabled = True
        
        self.lastActivityDateTime = datetime.now() - timedelta(days=365)
        self._lastPingDateTime = datetime.now() - timedelta(days=365) 
        
        self.alarmConnect = Alarm( f"{alarmName} {self.comPort}" )        
        self.lock = threading.Lock()
        self.serial = None
        
        self.nbConnectAttempts =  0
        
        
        self.reconnect = False
        
        self.pingMode = False
        
        
        self.readThread = threading.Thread(target=self.read , name = f"{self.comPort} COM Manager")
        self.readThread.start()
        
        
        self.hello()
    
    def enablePing(self):
        # this is to enable monitoring of port with ping calls.
        # typically for devices such as raspi that still communicate even if no code is running on the device.
        if self.pingMode == False:
            self.pingMode = True
            self._lastPingDateTime = datetime.now()
            self.pingThread = threading.Thread( target = self.pingLoop , name = f"{self.comPort} COM Manager - ping")
            self.pingThread.start()
            
    def pingLoop(self):
        while( self.enabled ):
            self.send("ping")
            sleep(1)
            
            if self.getNumberOfSecondSinceLastPing() > 2:
                self._alarmOn()
            else:
                self._alarmOff()
    
    def hotChangeComPort(self , newComPort ): # !!! experimental !!!
        
        self.enabled = False
        self.closeSerial()
        self.enabled = True
        self.comPort = newComPort        
        
        self.readThread = threading.Thread(target=self.read , name = f"{self.comPort} COM Manager")
        self.readThread.start()

    def isConnected(self):
        return self.connected
    
    
    def _activity(self):
        # if reading or writing activity is a success, calling this reset set the self.lastActivity datetime
        self.lastActivityDateTime = datetime.now()
    
    def getDelaySinceLastActivity(self):
        return datetime.now()- self.lastActivityDateTime 
        
    def closeSerial(self):
        
        if self.serial != None:
            
            self.serial.close()
            self.connected = False
        
    def _connect(self):
        
        self.closeSerial()
        
        connectOk = False
        while connectOk == False:
            try:                
                
                self.nbConnectAttempts+= 1
                self.closeSerial()
                self.serial = serial.Serial( port=self.comPort, baudrate=self.baudrate, bytesize=8, timeout=None )
                            
                self.serial.write_timeout = 0.5
                self.nbConnectAttempts = 0
                self._alarmOff()
                self.connected = True
                self.reconnect = False
                self.log("connected")

            except Exception as e:
                print(e )
                self.log(e)
                self.connected = False
                self._alarmOn()
                self.log( f"Trying to reconnect... nb reconnect attempts: {self.nbConnectAttempts}")                
                sleep(1)
        
            connectOk=True
                
    
    def addReceivedString( self, serialString ):
        self.readBuffer+=serialString
            
        self.readBuffer = self.readBuffer.replace("\r", "\n")
        while "\n" in self.readBuffer:
            
            i = self.readBuffer.find("\n")

            s = self.readBuffer[0:i]
            self.readBuffer = self.readBuffer[i+1:]             

            s = s.strip()
            
            if s.startswith("pong"):
                self.pongReceived()
            
            self.fireEvent( DeviceEvent( "ComManager" , self, s, data=self.comPort ) )
            
            
    
    def stop(self):
        if self.enabled:
            self.log("Com port auto exiting on quit.")
            self.enabled = False
        
    def shutdown(self):
        self.log("Com port shutdown")
        self.enabled = False
    
    def read(self):        
        
        while( self.enabled ):
            
            sleep(.001)
            

            if self.serial == None:
                self._connect()                
                continue                        
            
            if self.reconnect:
                self.log("read > reconnect started")
                self._connect()                
                continue
                
            
            try:
                bytesToRead = self.serial.inWaiting()

            except SerialException:
                self.log("disconnect in **in waiting** !")
                self._connect()
            
            if bytesToRead > 0:
            
                data = self.serial.read_all()

                try:
                    serialString = data.decode('utf-8')
                except:
                    # error in decode
                    self.log( f"Can't decode in utf-8: {data}")
                    serialString = ""
                    
                
                
                self.addReceivedString( serialString )
                
                self._activity()
                
            
        self.log(f"{self.comPort} stopped")
        if self.serial != None:
            self.serial.close()
            
    def _alarmOn(self):
        self.alarmConnect.sendAlarmMail( AlarmState.ALARM_ON , "disconnected." )
    
    def _alarmOff(self):
        self.alarmConnect.sendAlarmMail( AlarmState.ALARM_OFF , "re-Connected." )        
    
    def send(self, message ):
        
        if self.serial == None:
            return False
        
        try:
            self.lock.acquire()
        
            message+="\r\n"
            try:
                message = message.encode("utf-8")
            except:
                self.log("Error : Problem while encoding message in utf-8")
                return False
                                
            try:
                self.serial.write( serial.to_bytes( message ) )
                self._activity()
                return True
                        
            except serial.SerialException as e:
                self.log( f"Critical error: serial disconnected: can't write {message}" )
                sleep( 0.5 )
                self.connected = False
                self.reconnect = True
                self._alarmOn()
                return False
                
                    
                
        finally:
            self.lock.release()
    
        
    def fireEvent(self, deviceEvent ):
        
        for listener, kwargs in self.deviceListenerList:
            
            listener( deviceEvent, **kwargs )
            
    
    def addDeviceListener(self , listener, listener_kwargs ):
        self.deviceListenerList.append( (listener,listener_kwargs) )
        
    def removeDeviceListener(self , listener ):
        self.deviceListenerList.remove( listener )
    
    def log(self, message ):        
        logging.info( f"COM Manager: {self.comPort}: {message}")

    def hello(self):
        self.send("hello")
        
    def ping(self):
        self.send("ping")
    
    def pongReceived( self ):
        self._lastPingDateTime = datetime.now()    
    
    def getNumberOfSecondSinceLastPing(self):        
        
        delta = datetime.now()-self._lastPingDateTime
        return delta.total_seconds()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
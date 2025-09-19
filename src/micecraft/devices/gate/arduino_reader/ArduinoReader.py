'''
Created on 5 oct. 2021

@author: Fab
'''
import serial
import time
import threading
import logging

from time import sleep
from micecraft.soft.com_manager.ComManager import ComManager

class ArduinoReader(object):
    
    '''
    - Manage the scale connected with an arduino nano for the gate.
    - Manage LIDAR
    '''

    def __init__(self, comPort, name , weightFactor = 1 , invertScale = False ):        
        print("Starting balance and LIDAR controller",name,"reader on port " , comPort)
        self.weightFactor = weightFactor
        self.name = name
        self.invertScale = invertScale
        self.enabled = True
        self.comPort = comPort
        self.stopped = False
        self.weight = -1
        #self.lock = threading.Lock()    
        #self.comPort = comPort
        
        
        #self.connect()
        #self.ser = serial.Serial(comPort, 115200  )
        #self.flushData()
        self.readData = []
        self.listenerList = []

        self.comManager = ComManager( self.comPort, self.comListener, alarmName = "Arduino reader" ) #, baudrate=9600 )
        #thread = threading.Thread( target=self.monitor , name = f"Thread ArduinoReader - {self.name}")
        #thread.start()
    
    def log(self, message ): 
        s = f"Arduino reader (balance and lidar controller): {self.name} {self.comPort} {message}"
        #print( s )       
        logging.info( s )
    
    def connect(self):
        try:
            self.serialPort.close()
        except:
            # serial already close or object not initialized
            pass
        self.serialPort = serial.Serial( port=self.comPort, baudrate=115200, bytesize=8, timeout=None )
        self.serialPort.write_timeout = 0.5
        
    
    def comListener(self , event ):

        if not self.enabled:
            # add log here            
            return
                    
        if "init" in event.description:
            self.log( event.description )
                              
        
        if "ready" in event.description:
            self.log( event.description )
                            
        
        if "tare" in event.description:
            self.log( event.description )
            
        
        if "w:" in event.description:
            data = event.description.strip()
            try:
                value = round( float( data[2:] ) * self.weightFactor , 2 ) 
                self.fireWeightMeasure( value )
            except:                        
                logging.info("Error in weight read. Data received: " + event.description )
                
        if "lidar:" in event.description:
            try:
                data = event.description.strip()
                value = data[6:10] # example of message: lidar:0000"
                #print( value )
                self.fireLIDARMeasure( value )
            except:
                logging.info("Error in lidar read. Data received: " + event.description )
            
            
            
            
    '''
    def monitor(self):
        
        logging.info( "Balance monitoring started" )
        
        while( self.stopped == False ):            
            
            if self.enabled:
                
                time.sleep(0.001)
                
                data = self.readInput()
                if data == None:
                    continue
                
                if "init" in data:
                    print("Balance/LIDAR : ", self.name , data )
                    continue                  
                if "ready" in data:
                    print("Balance/LIDAR : ", self.name, data )
                    continue                
                if "tare" in data:
                    print("Tare : ", self.name, ":" , data )
                    continue
                
                if "w:" in data:
                    data = data.strip()
                    try:
                        value = round( float( data[2:] ) * self.weightFactor , 2 ) 
                        self.fireWeightMeasure( value )
                    except:                        
                        logging.info("Error in weight read. Data received: " + data)
                        
                if "lidar:" in data:
                    try:
                        data = data.strip()
                        value = data[6:10] # example of message: lidar:0000"
                        #print( value )
                        self.fireLIDARMeasure( value )
                    except:
                        logging.info("Error in lidar read. Data received: " + data)
                
                #print( "received data : " , value , " grams" )
    '''
                    
    def enableReading(self, enable ):
        self.enabled = enable
        
    def addListener(self , method ):
        self.listenerList.append( method )
    
    '''        
    def sendReadOrder(self):
        self.write("RAT")
    '''
        
    def fireWeightMeasure(self , weight ):
        #logging.info(f"Current Scale {self.comPort}:{self.name}: {str(weight)}")
        if self.invertScale:
            weight=-weight
        for listener in self.listenerList:            
            listener( weight=weight )
    
    
    def fireLIDARMeasure(self , lidarValues ):
        #print( self.listenerList )
        for listener in self.listenerList:
            listener( lidar = lidarValues )         
             
    '''           
    def flushData(self):
        try:
            self.lock.acquire()
            self.serialPort.flushInput()
        except:
            # fixme: add log
            self.lock.release()
    '''
    
    '''
    def readInput(self):
        
        try:
            self.lock.acquire()
            
            try:
                if self.serialPort.in_waiting > 0:
                            
                    serialString = self.serialPort.readline().decode("Ascii")                    
                    serialString = serialString.strip()
                    return serialString
                    
            except serial.SerialException as e:
                self.log( "Critical error: serial disconnected")
                self.alarmConnect.sendAlarmMail( AlarmState.ALARM_ON , "Arduino (balance lidar) disconnected." )                
                try:
                    self.connect()
                    self.log( "reconnect ok" )
                    self.alarmConnect.sendAlarmMail( AlarmState.ALARM_OFF , "Arduino (balance lidar) re-Connected." )
                except:
                    self.log( "Can't reconnect" )
                sleep( 1 )
            
        finally:
            self.lock.release()
        
            
        
    '''
    
    def isAlarmOn(self):
        
        if not self.comManager.isConnected():
            return "Device disconnected"
        
        return False
        
    def write( self, command ):
    
        self.comManager.send( command )
    
        '''
        try:
            self.lock.acquire()
            
            command+="\n"
            #print( "sending... " , message )
                            
            try:
                self.serialPort.write( command.encode("utf-8") )        
            except serial.SerialException as e:
                self.log( "Critical error: serial disconnected")
                self.alarmConnect.sendAlarmMail( AlarmState.ALARM_ON , "Arduino (balance / lidar control) disconnected." )                
                try:
                    self.connect()
                    self.log( "reconnect ok" )
                    self.alarmConnect.sendAlarmMail( AlarmState.ALARM_OFF , "Arduino (balance / lidar control) re-Connected." )
                except:
                    self.log( "Can't reconnect" )
                sleep( 1 )
            
        finally:
            self.lock.release()
        '''
        
        
        '''
        command+="\r"
        command= command.encode("utf_8")
        self.lock.acquire()
        #print( "Sending command : " , command )        
        self.lock.release()
        '''
    
    def tare(self):
        self.write("tare")
                
    def close(self):    
        self.stopped = True
        time.sleep( 0.1 )
        #self.serialPort.close()
        self.comManager.shutdown()
        print( "Balance " , self.name , "stopped")

if __name__ == '__main__':
    
    def listener( weight ):
        print( "Data received by listener: " , weight )
        
    print("Testing balance")
    balance = ArduinoReader("COM81" , "Testing balance")
    balance.addListener( listener )
    
    time.sleep( 60 )
    
    '''
    balance.tare()
    balance.tare()
    balance.tare()
    time.sleep( 5 )
    balance.tare()
    time.sleep( 5 )
    balance.tare()
    time.sleep( 5 )
    balance.close()
    '''
    
    
    
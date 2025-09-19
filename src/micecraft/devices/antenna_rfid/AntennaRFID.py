'''
Created on 24 sept. 2021

@author: Fabrice de Chaumont
'''

import time
import threading
import logging

from time import sleep
import atexit
from micecraft.soft.ComManager.ComManager import ComManager

class AntennaRFID(object):
    
    def __init__(self, comPort, startReading = True, readTuningFrequency=False ):
    
    
        self.readData = []
        self.stopped = False
        self.frequency = 0
        self._readingFrequency = False
        self._readingSerialNumber = False
        self.comPort = comPort
        self.listenerList = []
        self.serialNumber = None
        
        self.antennaFieldActive = False
        self.hasReadAnRFID = False
        
        self.comManager = ComManager( self.comPort, self.comListener, alarmName = "RFID Antenna", baudrate= 9600 )
                
        if readTuningFrequency:
            self.readFrequency() # read tuning frequency
                
        self.write( "ST2" ) # Set read animal tags.
        self.write( "SB1" ) # Disable read buzzer
        self.write( "SL4" ) # Leds off
        self.switchOff()
        
        self.enableReading( startReading )
        
        thread = threading.Thread( target=self.monitor , name= f"Thread AntennaRFID - {comPort}")
        thread.start()
                
        self.readSerialNumber()            
            
        atexit.register(self.close)
    
    def enableReading(self, enable ):
        self.enabled = enable
        
    def addListener(self , method ):
        self.listenerList.append( method )
    
    
    def comListener(self , event ):
        
        if not self.stopped:

            if self._readingSerialNumber:
                if len( event.description ) != 4:
                    pass
                    #print(f"junk: {event.description}")
                else:
                    #print(f"---------- READ SERIAL NUMBER:  {event.description}")
                    self.serialNumber = event.description                
                    self._readingSerialNumber = False
                
            
            if self._readingFrequency:
                self.frequency = event.description
                self.log( f"tuning frequency: {event.description}")
                self._readingFrequency = False
            
            for s in event.description.split("_"):
                if len(s)==12:
                    
                    #self.log( f"ok rfid step len 12:  {event.description} --> {s}" )
                    if s.isdigit(): # )"?" not in s
                        self.fireRFIDFound( s )
                        self.hasReadAnRFID = True
                        #self.readState ="RFID READ"            

    
    def monitor(self):
                
        while( self.stopped == False ):            
                        
            if self._readingFrequency: # should not read chip while waiting for tuning info
                time.sleep(0.1)
                continue
            
            if self._readingSerialNumber:
                time.sleep(0.1)

                self.write("RSN")    

                continue
                
            if self.enabled:
                
                if self.antennaFieldActive == False:
                    
                    self.switchOff()
                    self.switchOn()
                
                if self.hasReadAnRFID:
                    self.hasReadAnRFID = False
                    self.sendReadOrder()
                        
            else:
                self.switchOff()      
                time.sleep(0.1)
            
        
    def fireRFIDFound(self , rfid ):
        for listener in self.listenerList:
            logging.info("Sending RFID fire to listeners: " + str( listener ) )
            listener( rfid )
        
        
    def setSerialNumber(self , serial ):
        
        if len( serial ) != 4:
            print( "RFIDAntenna : can't program the chip, the serial number must be 4 alphanum chars")
            return        
        
        hex_digits = set("0123456789abcdef")
        for c in serial.lower():
            if not (c in hex_digits):
                print( f"RFIDAntenna : can't program the chip, the value '{c}' in {serial} is not hex (between 0-F)" )
        
        if not serial.isalnum():
            print( "RFIDAntenna : can't program the chip, the serial number must only contain alphanumeric chars")
            return        
                
        self.write(f"SSN{serial}")
    
    
    def readSerialNumber(self ):
        # default serial number in readers is 1234        
        self._readingSerialNumber = True        
    
    def isSerialNumberReady(self ):
        return self.serialNumber != None
        
    def getSerialNumber(self ):
        if self.serialNumber == None:
            self.readSerialNumber()
                
        while( self.serialNumber == None ):
            sleep(0.2)
        
        return self.serialNumber
        

        
    def readFrequency(self):
        self.switchOn()
        time.sleep(0.3)

        self.write("MOF")
        self._readingFrequency = True
        time.sleep(2)
        # the tuning number will arrive in this interval by the ComManagerListener
        self._readingFrequency = False
                                
        self.switchOff()
    
    def log(self, message ):        
        logging.info( f"Antenna: {self.comPort} {message}")
        
    def write( self, command ):
        
        self.comManager.send( command )
        self.readOrder = command

    
    def isConnected(self):
        return self.comManager.isConnected()
    
    def isAlarmOn(self):
        
        if not self.comManager.isConnected():
            return "Device disconnected"
        
        return False
       
                
    def sendReadOrder(self):
        self.write("RAT")
        time.sleep(0.01)
        
    def switchOn(self):
        self.antennaFieldActive = True
        self.write("SRA")        
        time.sleep(0.1)
        
    def switchOff(self):
        self.antennaFieldActive = False
        self.write("SRD")        
        time.sleep(0.01)
        
    def close(self):    
        self.stopped = True
        time.sleep( 0.1 )
        self.comManager.shutdown()
        
        
    def getTuningFrequency(self):
        return self.frequency


    
    
    
    
    
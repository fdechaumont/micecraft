'''
Created on 23 sept. 2021

@author: Fab
'''

import time
import threading

from enum import Enum
    

import numpy as np
import inspect
from datetime import datetime
import logging

from inspect import getframeinfo, stack


import socket

import traceback

from micecraft.devices.gate.Parameters import MAX_GATE_WEIGHT_LIST_SIZE,\
    CLOSED_DOOR_POSITION_RAT, CLOSED_DOOR_POSITION_MOUSE,\
    OPENED_DOOR_POSITION_RAT, OPENED_DOOR_POSITION_MOUSE, NB_OBSERVATION_RFID,\
    DEFAULT_TORQUE_AND_SPEED_LIMIT_MOUSE, DEFAULT_TORQUE_LIMIT_RAT,\
    DEFAULT_SPEED_LIMIT_RAT, NB_VALUE_TO_COMPUTE_MEAN_WEIGHT,\
    NB_OBSERVATION_WEIGHT
from micecraft.devices.antenna_rfid.AntennaRFID import AntennaRFID
from micecraft.devices.gate.Door import Door
from micecraft.soft.device_event.DeviceEvent import DeviceEvent

def getCaller():
    
    all_stack_frames = inspect.stack()
    answer = ""    
    answer += all_stack_frames[2][3] + " / "
    answer += all_stack_frames[3][3] + " / "
    answer += all_stack_frames[4][3] + " / "
    
    #for n in caller_stack_frame:
    #    print ( n )
    
    return answer

class GateMode(Enum):
    MOUSE = 1
    RAT = 2
    
            
class GateOrder(Enum):
    ALLOW_SINGLE_A_TO_B = 1
    ALLOW_SINGLE_B_TO_A = 2
    ONLY_ONE_ANIMAL_IN_B = 3
    ONLY_ONE_ANIMAL_IN_A = 11
    NO_ORDER = 4
    OPEN_CLOSE_HABITUATION = 5
    ALLOW_MULTIPLE_A_TO_B = 6
    ALLOW_MULTIPLE_B_TO_A = 7
    EMPTY_IN_A = 8
    EMPTY_IN_B = 9
    TEST_RFID_GATE_MODE = 10

class WaitForSecondLogic(): # check if only 1 animal is present
    
    def __init__(self, gate , seconds ):
        self.done = False
        self.error = False
        self.seconds = float( seconds )
        '''
        self.observationTime = 6 # number of observation ( 1 observation = 1/10 of second )
        self.gate = gate
        self.weightList = []
        '''
        self.startTime = datetime.now()        
    
    def process(self):

        now  = datetime.now()
        diff = (now-self.startTime ).total_seconds()
        #print( "Waiting... " , diff )
        if diff > self.seconds:
            self.done = True                

class CheckForOneAnimalLogic(): # check if only 1 animal is present
    
    def __init__(self, gate ):
        self.observationTime = NB_OBSERVATION_WEIGHT # number of observation
        self.done = False        
        self.error = False
        self.gate = gate
        self.weightList = []        
    
    def process(self):
                
        self.weightList.append( self.gate.getCurrentWeight() )        
        self.observationTime-=1
        #print( self.weightList )
        
        if self.observationTime < 0:
            mean = np.mean( self.weightList[-NB_VALUE_TO_COMPUTE_MEAN_WEIGHT:] )
            logging.info(f"CheckForOneAnimalLogic: Mean weight : {str(mean)}" )
            if self.gate.isWeightOfOneMouse( mean ):
                info = self.gate.name + " CheckForOneAnimalLogic WEIGHT OK: " + str( mean )
                logging.info( info )
                self.gate.setLastAnimalWeight( mean )
                self.gate.fireEvent( DeviceEvent( "gate", self.gate, info ) )
                self.done = True                
            else:
                info = self.gate.name + " CheckForOneAnimalLogic WEIGHT ERROR: " + str( mean ) 
                logging.info( info )
                self.gate.fireEvent( DeviceEvent( "gate", self.gate, info ) )
                self.error = True            

            
class CheckNoAnimalLogic():
    
    def __init__(self, gate ):
        self.observationTime = NB_OBSERVATION_WEIGHT # number of observation ( 1 observation = 1/10 of second )
        self.done = False
        self.error = False
        self.gate = gate
        self.weightList = []        
    
    def process(self):
                
        self.weightList.append( self.gate.getCurrentWeight() )        
        self.observationTime-=1
        
        if self.observationTime < 0:
            mean = np.mean( self.weightList[-NB_VALUE_TO_COMPUTE_MEAN_WEIGHT:] )
            #logging.info(f"CheckNoAnimalLogic: Mean weight : {str(mean)}"  )        
            #print("CheckNoAnimalLogic: Mean weight : " , mean )            
            if mean < self.gate.mouseAverageWeight /4:
                self.done = True
                #logging.info(f"CheckNoAnimalLogic: Mean weight : Ok No animal."  )
            else:
                self.error = True
                #logging.info(f"CheckNoAnimalLogic: Mean weight : Animal is still present "  )
            
        
class CheckAnimalIdLogic(): # check if only 1 animal is present
    
    def __init__(self, gate, sideText ):
        self.maxNbObservationRFID = NB_OBSERVATION_RFID
        self.observationTime = self.maxNbObservationRFID # number of observation ( 1 observation = 1/10 of second )
        self.done = False
        self.error = False
        self.gate = gate
        self.sideText = sideText   
        self.lastProcessCall = datetime.now()
        self.startTime = datetime.now()
        
    def process(self):

        lastCall = ( datetime.now() - self.lastProcessCall ).total_seconds()
        self.lastProcessCall = datetime.now()
        
        dt = datetime.now()
        #logging.info( f"start CheckAnimalIdLogic (last call) {lastCall} s" );
        if self.gate.rfidControlEnabled:
            self.gate.antennaRFID.enableReading( True )
            self.gate.LMT_RFIDStop()
        
        if self.gate.rfidControlEnabled == False: # accept all
            print( f"RFIDCONTROL ENABLED: {self.gate.rfidControlEnabled}") 
            self.done = True
            self.error = False
            return
        
        self.observationTime-=1
        
        info = "[RFID CHECK]["+self.gate.name+"] Checking RFID: remaining attempts: " + str ( self.observationTime )
        logging.info( info );
        self.gate.fireEvent( DeviceEvent( "gate", self.gate, info ) )
        
        duration= (datetime.now()-dt).total_seconds()
        #logging.info( f"end CheckAnimalIdLogic {duration}" );
        
        #logging.info( "["+self.name + "] rfid list size: " + str( len( self.gate.RFIDDetectionList ) ) );
        
        # avoid spamming of RFID read        
        nbRFIDreading = len( self.gate.RFIDDetectionList ) 
        '''
        if nbRFIDreading > 0:
            logging.info( f"nb rfid read received: {nbRFIDreading}")
        '''
        rfidDetectedListUnSpammed = list(set( self.gate.RFIDDetectionList )) # remove all doublons
        
        self.gate.RFIDDetectionList.clear()
        
        for rfid in rfidDetectedListUnSpammed:
            #self.gate.RFIDDetectionList.remove(rfid)
            logging.info("parsing rFIDs..")
            duration = ( datetime.now() - self.startTime ).total_seconds()
            info = f"[RFID CHECK][{self.gate.name}] RFID {rfid} read in: {self.maxNbObservationRFID-self.observationTime} / {self.maxNbObservationRFID} time: {duration:.2f} seconds side: {self.sideText}"
            logging.info( info )   
            
            '''
            if self.gate.gateRFIDCheckCallBack != None:
                auth = self.gate.gateRFIDCheckCallBack( rfid, self.sideText )
                
                # fixme: with the callback, bypass all list and accept the RFID.
                # at the moment the callback only works for animal not allowed
                if auth == False:
                    info = f"[RFID CHECK][{self.gate.name}] Animal forbidden to cross (by gateRFIDCheckCallBack): {rfid} {self.sideText}"
                    logging.info( info )
                    self.gate.antennaRFID.enableReading(False)
                    self.error = True                                
                    self.gate.fireEvent( DeviceEvent( "gate", self.gate, info , data=rfid ) )
                    return
            '''
             
            if rfid in self.gate.forbiddenRFIDList:
                info = f"[RFID CHECK][{self.gate.name}] Animal forbidden to cross: {rfid} {self.sideText}"
                logging.info( info )
                self.gate.antennaRFID.enableReading(False)
                self.error = True                                
                self.gate.fireEvent( DeviceEvent( "gate", self.gate, info , data=rfid ) )
                return
            
            #[ "001043406172", "001043406139", "001043406183", "001043406146", "001043406158", "001043406195" ]
            if len ( self.gate.rfidAllowedList ) > 0:
                if rfid not in self.gate.rfidAllowedList:
                    info = f"[RFID CHECK][{self.gate.name}] Animal not in allowed list: {rfid} {self.sideText}"
                    logging.info( info )
                    self.gate.antennaRFID.enableReading(False)
                    self.error = True                                
                    self.gate.fireEvent( DeviceEvent( "gate", self.gate, info , data=rfid ) )
                    return
            
            # the RFID was not in the forbidden list. Pass.
            info = f"[RFID CHECK][{self.gate.name}] Animal allowed to cross: {rfid} {self.sideText}"
            logging.info( info )
            self.gate.antennaRFID.enableReading(False)
            self.done=True
            #cm = CodeMonitoring("fire event gate found rfid")
            self.gate.fireEvent( DeviceEvent( "gate", self.gate, info, data=rfid ) )
            #cm.read("step 1")
            self.gate.fireEvent( DeviceEvent ( "gate" , self.gate , f"animal weight:{rfid}:{self.gate.lastAnimalWeight}") )
            #cm.read("step 2")            
            self.gate.addScaleMeasurement( rfid, self.gate.lastAnimalWeight )
            #cm.read("step 3")
                                
            return                
               
        if self.observationTime < 0:            
            self.error = True
            self.gate.antennaRFID.enableReading(False)
            info = "[RFID CHECK]["+self.gate.name+"]Checking RFID: Can't read ID of animal (or multiple ID present ?)"
            logging.info( info )
            self.gate.fireEvent( DeviceEvent( "gate", self.gate, info ) )
            return

        return



    
class Gate(object):
    '''
    A gate manage 2 doors
    '''

    def __init__(self, COM_Servo=None, COM_Arduino=None, COM_RFID=None, name="noName gate" , weightFactor = 1 , mouseAverageWeight = 25, enableLIDAR = True , lidarPinOrder = None , gateMode = GateMode.MOUSE, invertScale = False ):        
        
        print('Gate init..')


        self.lock = threading.Lock()
        self.allowOverWeight = False
        self.rfidControlEnabled = False
        self.antennaRFID = None
        self.arduino = None
        
        self.COM_Servo = COM_Servo
        self.COM_RFID = COM_RFID
        self.COM_Arduino = COM_Arduino
        self.enableLIDAR = enableLIDAR
        self.lidarPinOrder = ( 0, 1, 2 , 3 )
        self.name = name
        self.currentWeight = 0
        self.forcedWeightValue = None # if this value is set, the gate will always "see" this value. For test purposes only.
        self.forcedRFIDDetection = None # if this value is set, the gate will always "see" this RFID value as a reading. For test purposes only.
        self.weightFactor = weightFactor # correction factor applied to the measurement of the balance. This value is component dependent and should be set for each gate 
        self.mouseAverageWeight = mouseAverageWeight # in grams
        self.weightList = [] # a list containing the last 10 reading of weight recorded. Last is newest
        self.lastAnimalWeight = None # the last weight recorded when the check one animal process ran
        self.scaleMeasurements = {} # a dictionary with all measurements. rfid is key and then tuple ( datetime , weight )
        self.scaleShift = 0 # this value is added to any read from the scale.
        self.order = GateOrder.NO_ORDER
        
        self.forbiddenRFIDList=[]
               
        self.rfidAllowedList = [] 
        
        self.state = None
        self.logicList = []
        self.logicCursor = 0
        self.setLogicProcess( None ) #self.logicProcess = None        
        self.previousLogic = None
        self.previousTime = 0
        #self.lock = threading.Lock()
        self.motorManager = None
        
        self.LMTSideA = None
        self.LMTSideB = None

        self.gateRFIDCheckCallBack = None

        
        self.lastRecordedRFID = None # used to communicate which animal is getting where (to provide LMT extra info on present animals )

        self.chronoPlayLogic = datetime.now()

        try:
            self.motorManager = MotorManager( COM_Servo )
        
        except:
            print("Quit: Can't connect motors using port: " , COM_Servo )            
            self.shutdown()
            quit()
         
        
        
        self.doorA = Door( Ax12Motor(1, self.motorManager) , "A "+name , enableLIDAR )
        self.doorB = Door( Ax12Motor(2, self.motorManager) , "B "+name , enableLIDAR )                    
        
        
        if COM_Arduino!=None:
            try:
                self.arduino = ArduinoReader(COM_Arduino , "arduino " + self.name , weightFactor = self.weightFactor, invertScale = invertScale )
            except:
                print("Quit: Can't connect to arduino using port: " , COM_Arduino )
                self.shutdown()
                quit()
            self.arduino.addListener( self.balanceLIDARListener )
        self.weightWindowFactor = 0.3
                
        self.gateMode = gateMode
        
        if self.gateMode == GateMode.MOUSE:
            self.doorA.setLimits( OPENED_DOOR_POSITION_MOUSE, CLOSED_DOOR_POSITION_MOUSE )
            self.doorB.setLimits( OPENED_DOOR_POSITION_MOUSE, CLOSED_DOOR_POSITION_MOUSE )
            self.setSpeedAndTorqueLimits(DEFAULT_TORQUE_AND_SPEED_LIMIT_MOUSE, DEFAULT_TORQUE_AND_SPEED_LIMIT_MOUSE)
        
        
        if self.gateMode == GateMode.RAT:
            self.doorA.setLimits( OPENED_DOOR_POSITION_RAT, CLOSED_DOOR_POSITION_RAT )
            self.doorB.setLimits( OPENED_DOOR_POSITION_RAT, CLOSED_DOOR_POSITION_RAT )
            self.setSpeedAndTorqueLimits(DEFAULT_SPEED_LIMIT_RAT, DEFAULT_TORQUE_LIMIT_RAT)
            self.doorA.keepTorqueActiveWhileDoorAreClosed = True
            self.doorB.keepTorqueActiveWhileDoorAreClosed = True
            #self.setSpeedAndTorqueLimits( 30, 400 ) #1000
            
        
        self.stopped = False
        self.RFIDDetectionList = []        
        self.rfidControlEnabled = False
        
        if COM_RFID != None:
            try:
                self.antennaRFID = AntennaRFID( COM_RFID )
                self.antennaRFID.addListener( self.rfidDetectionListener )
                logging.info("Adding listener for gate: " + str ( self.rfidDetectionListener ) )
                self.rfidControlEnabled= True
                self.antennaRFID.enableReading( False )
                 
            
            except:
                print("Quit: Can't connect RFID reader using port: " , COM_RFID )
                self.shutdown()
                quit()
            
                
        self.deviceListenerList = []
        
        if lidarPinOrder !=None:
            self.setLidarPinOrder(lidarPinOrder)
        
        self.addDeviceListener( self.listener )
        self.setSecurityLevel()
        
        self.thread = threading.Thread( target=self.monitor , name= f"Gate Thread - {self.name}" )
        self.thread.start()
        
        self.thread2 = threading.Thread( target=self.monitor2 , name= f"Gate Thread2 - {self.name}" )
        self.thread2.start()

        time.sleep(1)
        print('Gate started. name=' + name )
        
    def setSecurityLevel(self , securityLevel=2 ):
        
        '''        
        In the door jam logic, for each door, we have 2 lidars. One in, one outside the corridor.
        In security 2, the jam is activated (meaning the gate will not close) if the 2 lidars are detecting an obstacle.
        In security level 3, the jam is activated if any of the 2 lidars is detection an obstacle.
        
        Level 3 is recommended when you have only one animal.
        If you have a lot of animals, then level 3 may result in having animal outside the gate that can
        prevent the gate from closing because the animal is against the door.
        
        Default security level is 2.         
        '''
        
        self.securityLevel = securityLevel
        self.doorA.securityLevel = securityLevel
        self.doorB.securityLevel = securityLevel
        
    def setNbObservationRFID(self, nbObservationRFID = NB_OBSERVATION_RFID ):
        self.nbObservationRFID = nbObservationRFID
        
        
        
    def setGateRFIDCheckCallBack(self , gateRFIDCheckCallBack ):
        self.gateRFIDCheckCallBack = gateRFIDCheckCallBack

        
    def setLastAnimalWeight(self , weight ):
        self.lastAnimalWeight = weight
    
    def addScaleMeasurement( self, rfid, weight ):
        if rfid not in self.scaleMeasurements:
            self.scaleMeasurements[rfid] = []
        self.scaleMeasurements[rfid].append( ( datetime.now() , weight ) )

    def setLimitsOffset(self , openOffset=None, closeOffset=None ):
        # to close less the gate, set the closeOffset to a negative value 
        
        self.doorA.setLimits( OPENED_DOOR_POSITION_RAT, CLOSED_DOOR_POSITION_RAT )
        self.doorB.setLimits( OPENED_DOOR_POSITION_RAT, CLOSED_DOOR_POSITION_RAT )
        
        open = None
        close = None
        if self.gateMode == GateMode.MOUSE:
            open = OPENED_DOOR_POSITION_MOUSE
            close = CLOSED_DOOR_POSITION_MOUSE
        if self.gateMode == GateMode.RAT:
            open = OPENED_DOOR_POSITION_RAT
            close = CLOSED_DOOR_POSITION_RAT
        
        if openOffset != None:
            open+=openOffset
        if closeOffset != None:
            close+=closeOffset
            
        #OPENED_DOOR_POSITION_MOUSE = 110
        #CLOSED_DOOR_POSITION_MOUSE = 290

        self.doorA.setLimits( open, close )
        self.doorB.setLimits( open, close )


    def listener(self , event ):
        
        '''
        if "Animal allowed to cross" in event.description:
            
            print ( "LISTENER reading: " + str ( event ) )
            rfid = event.data
            if self.getOrder() == GateOrder.ALLOW_SINGLE_A_TO_B:
                
                if self.LMTSideA != None:
                    self.LMT_sendRFIDInfoForArea( self.LMTSideA.ip , rfid , False ) # The animal is leaving the setup on A side

                if self.LMTSideB != None:
                    self.LMT_sendRFIDInfoForArea( self.LMTSideB.ip , rfid , True ) # The animal is coming in the setup on B side

            if self.getOrder() == GateOrder.ALLOW_SINGLE_B_TO_A:
                
                if self.LMTSideA != None:
                    self.LMT_sendRFIDInfoForArea( self.LMTSideA.ip, rfid , True ) # The animal is coming in the setup on A side

                if self.LMTSideB != None:
                    self.LMT_sendRFIDInfoForArea( self.LMTSideB.ip, rfid , False ) # The animal is leaving the setup on B side
        '''
        if "Animal allowed to cross" in event.description:
            rfid = event.data
            #2023-12-14 19:03:16.431: [RFID CHECK][collab gate A] Animal allowed to cross: 001043763393 TO SIDE B
            
            if "TO SIDE A" in event.description:
                
                if self.LMTSideA != None:
                    self.LMT_sendRFIDInfoForArea( self.LMTSideA.ip, rfid , True ) # The animal is coming in the setup on A side

                if self.LMTSideB != None:
                    self.LMT_sendRFIDInfoForArea( self.LMTSideB.ip, rfid , False ) # The animal is leaving the setup on B side
            
            if "TO SIDE B" in event.description:
                if self.LMTSideA != None:
                    self.LMT_sendRFIDInfoForArea( self.LMTSideA.ip , rfid , False ) # The animal is leaving the setup on A side

                if self.LMTSideB != None:
                    self.LMT_sendRFIDInfoForArea( self.LMTSideB.ip , rfid , True ) # The animal is coming in the setup on B side

            
            
        
                
    def setLMTSideA(self , lmtSideA ):
        self.LMTSideA = lmtSideA
    
    def setLMTSideB(self , lmtSideB ):
        self.LMTSideB = lmtSideB
             
    def alarmListener(self , event ):
        
        logging.info( event )        
                    
    def setAllowOverWeight(self , enableOverWeight ):
        self.allowOverWeight = enableOverWeight

    def LMT_RFIDStop( self ):
        # will stop RDID reading for 1 second
        
        UDP_IP = "127.0.0.1"
        UDP_PORT = 8552
        
        logging.info( "["+ str( self.name ) + "] stopping LMT RFIDs")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(bytes("rfid stop " + self.name , "utf-8"), (UDP_IP, UDP_PORT))
        sock.close()


    def LMT_sendRFIDInfoForArea( self, ip, rfid , enable ):
        # will send an RFID to the arena to tell which RFID has been through
        # enable > will send that the animal is entering the arena
        
        UDP_IP = ip
        UDP_PORT = 8553
        
        command = f" gate name: {self.name} : rfid"
        if enable:
            command +=" in"
        if not enable:
            command +=" out"
            
        command+=f" *{rfid}*"
        
        print(f"Sending command to LMT at {ip} for RFID identity presence: {command}" )
                
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(bytes( command  , "utf-8"), (UDP_IP, UDP_PORT))
        sock.close()

    def tare(self):
        logging.info( f"{self.name} taring... current weight:*{self.currentWeight}*list:*{self.weightList}*"   )
        if self.scaleShift != 0:
            logging.info( f"{self.name} taring... Scale shift removed ( set to 0 )"   )
            self.scaleShift = 0
        
        self.arduino.tare()
        
    def setScaleShift( self , scaleShift ):
        logging.info( f"{self.name} scale shift set to {scaleShift}" )        
        self.scaleShift = scaleShift

    def setLidarPinOrder(self, lidarPinOrder ):
        self.lidarPinOrder = lidarPinOrder
    
    def balanceLIDARListener( self, weight=None , lidar=None ):
        #print( "Data received by balance listener: " , weight )
        
        if weight!=None:            
            self.lock.acquire()
            weight += self.scaleShift
            if self.forcedWeightValue != None:
                weight = self.forcedWeightValue        
            self.weightList.append( weight )
            self.currentWeight = weight
            # check if the list is too long.
            if len( self.weightList ) > MAX_GATE_WEIGHT_LIST_SIZE:
                self.weightList.pop( 0 ) # remove first element (oldest)
            self.lock.release()
        
        if lidar != None:
            #print( "lidar data:" , lidar, self.lidarPinOrder )
            if lidar[self.lidarPinOrder[0]]=="0":
                self.doorA.lidarExt=False
            else:
                self.doorA.lidarExt=True


            if lidar[self.lidarPinOrder[1]]=="0":
                self.doorA.lidarIn=False
            else:
                self.doorA.lidarIn=True


            if lidar[self.lidarPinOrder[2]]=="0":
                self.doorB.lidarIn=False
            else:
                self.doorB.lidarIn=True


            if lidar[self.lidarPinOrder[3]]=="0":
                self.doorB.lidarExt=False
            else:
                self.doorB.lidarExt=True

            
    def forceWeightValue(self , value ):
        logging.info( f"{self.name} Force weight value to {value}")
        self.forcedWeightValue = value
        
    def disableForcedWeightValue(self ):
        logging.info( f"{self.name} Disable forced weight")
        self.forcedWeightValue = None
        
    def forceRFIDDetection(self , value ):
        logging.info( f"{self.name} Force RFID value to {value}")
        self.forcedRFIDDetection = value
        
    def disableForcedRFIDDetection(self):
        logging.info( f"{self.name} Disabled forced RFID")
        self.forcedRFIDDetection = None
        
    def getCurrentWeight(self):        
                
        #self.lock.acquire()
        return self.currentWeight
        #self.lock.release()
        
    def setForbiddenRFIDList(self , rfidList ):    
        self.lock.acquire()            
        self.forbiddenRFIDList = rfidList
        self.lock.release()
                
    def addForbiddenRFID(self ,rfid ):        
        self.lock.acquire()
        if rfid not in self.forbiddenRFIDList:        
            self.forbiddenRFIDList.append( rfid )
        self.lock.release()

    def removeForbiddenRFID(self ,rfid ):
        self.lock.acquire()
        if rfid in self.forbiddenRFIDList:
            self.forbiddenRFIDList.remove( rfid )
        self.lock.release()
        
    def setAllowedRFIDList(self , rfidList ):    
        self.lock.acquire()            
        self.rfidAllowedList = rfidList
        self.lock.release()
                
    def addAllowedRFID(self ,rfid ):        
        self.lock.acquire()
        if rfid not in self.rfidAllowedList:        
            self.rfidAllowedList.append( rfid )
        self.lock.release()

    def removeAllowedRFID(self ,rfid ):
        self.lock.acquire()
        if rfid in self.rfidAllowedList:
            self.rfidAllowedList.remove( rfid )
        self.lock.release()

    
    def autoCalibrate(self):
        self.doorA.calibrate()
        self.doorB.calibrate()
        
    def rfidDetectionListener(self, rfid ):    
        #logging.info( "GATE receive RFID info" )
        #logging.log( "RFID found in gate: " , self.name , ":" , rfid )
        #self.lock.acquire() #removed 14082025
        self.RFIDDetectionList.append( rfid )
        #self.lock.release() #removed 14082025
        #logging.info("RFID detected in gate: " + str( rfid ) )
    
    def debugCallerInfo( self ):
        caller = getframeinfo(stack()[2][0]) # 2 function before in the stack.
        return caller.filename +":"+ str( caller.lineno)
    
    def passToNextLogic(self):
        self.logicCursor +=1
        if self.logicCursor>=len( self.logicList ):
            self.logicCursor = 0
        #logging.info( "[NEXTLOGIC DEBUG] ["+ str( self.logicCursor ).zfill(3 ) + "] " + self.getLogic() )
        #logging.info( self.debugCallerInfo() )
    
    def getLogic(self):
        if len( self.logicList ) == 0:
            return None
        return self.logicList[self.logicCursor]
    
    def setSpeedAndTorqueLimits(self, speedLimit , torqueLimit):
        self.doorA.setSpeedAndTorqueLimits( speedLimit , torqueLimit)
        self.doorB.setSpeedAndTorqueLimits( speedLimit , torqueLimit)
        
    
    def setTorqueEnabled(self, enabled ):
        self.doorA.setTorqueEnabled( enabled )
        self.doorB.setTorqueEnabled( enabled )
    
        
    def getGotoLabelIndex(self, label ):
        
        for s in self.logicList:
            if label+":" in s:
                return self.logicList.index( s )
        print("Logic error: label not found : ", label )
        quit()
        
    def checkLogic(self):
        # check multiple labels
        dicLabel = {}
        for logic in self.logicList:
            if ":" in logic:
                s = logic.split(":")
                if len(s) > 0:
                    label = s[0]
                    #print( label )
                    if label in dicLabel:
                        print("Error in logic. Double label: name: " , label )
                        quit()
                    dicLabel[label]=True                    
        print( "Logic control check ok." ) 

    def getErrorGoto(self,logic):
        # find the error goto parameter in a logic string order
        li = logic.split(" ")
        for i in range( len( li ) ):
            s = li[i]
            if "ERRORGOTO" in s:
                return self.getGotoLabelIndex( li[i+1] )
    
    def getGoto(self,logic):
        # find the error goto parameter in a logic string order
        li = logic.split(" ")
        for i in range( len( li ) ):
            s = li[i]
            if "GOTO" in s:
                return self.getGotoLabelIndex( li[i+1] )        
    
    def isWeightOfOneMouse(self , weight ):
        
        if self.allowOverWeight:
            if weight > self.mouseAverageWeight * (1-self.weightWindowFactor):
                return True
                
        if weight > self.mouseAverageWeight * (1-self.weightWindowFactor) and weight < self.mouseAverageWeight*(1+self.weightWindowFactor):
            return True
        return False
    
    def isWeightAtLeastOneMouse(self , weight ):        
        if weight > self.mouseAverageWeight * (1-self.weightWindowFactor):
            return True
        return False
            
    def setLogicProcess(self , value ):
        #self.lock.acquire()
        self.logicProcess = value
        #self.lock.release()
        
    def playLogic(self):
        
        # log logic 
        
        if self.previousLogic != self.getLogic():        
            traceLogic = "[TraceLogic]["+self.name+"][" + str( self.logicCursor ).zfill(3) +"] " + str ( self.getLogic() )
            logging.info( traceLogic )
            self.fireEvent( DeviceEvent( "gate", self, traceLogic ) )
            self.previousLogic = self.getLogic()
        
        # shut down antenna if no process is active. Made by default to avoid a remaining on antenna if an order has been changed during the reading RFID process. Could be enhanced..
        if self.logicProcess == None and self.antennaRFID != None:            
            self.antennaRFID.enableReading(False)
            self.RFIDDetectionList.clear()
         
        # execute special logic processing
        
        try:
            self.lock.acquire() # to avoid problem with a change in the logicProcess while running this piece of code
            if self.logicProcess !=None:
                #print( "Current cursor / logic: " , self.logicProcess )
                
                self.logicProcess.process()
                
                if self.logicProcess.done:     
                    #print( "LOGIC PROCESS: DONE")
                    self.logicProcess = None # this is a direct access to the logicProcess within the lock acquire           
                    self.passToNextLogic()
                
                elif self.logicProcess.error:
                    #print( "LOGIC PROCESS: ERROR")     
                    self.logicProcess = None
                    logic = self.getLogic()
                    if "ERRORGOTO" in logic:
                        value = self.getErrorGoto(logic)                              
                        self.logicCursor = value
                        
                return
        except:
            #print ("The logicProcess has been changed during process")
            logging.info("CRITICAL ERROR in processing process script in gate: ")
            logging.info(traceback.format_exc())
        finally:
            self.lock.release()
        
            
            
        
        # run logic list
        
        logic = self.getLogic()
        
        #print( "Current cursor / logic: " , self.logicCursor, " : " , logic )
        
        if logic == None:
            return
        
        if "SETORDER NO_ORDER" in logic:
            self.setOrder( GateOrder.NO_ORDER )            
            return
        
        if "LOG" in logic:
            logging.info( "[Logic] " + self.name + " " + logic[3:] )            
            self.fireEvent( DeviceEvent( "gate", self, logic[3:] ) ) # todo: ajouter RFID et poids ?                        
            self.passToNextLogic()
            
        if "CLOSE" in logic:
            if "DOOR_A" in logic:                
                self.doorA.close()
                self.passToNextLogic()
            if "DOOR_B" in logic:
                self.doorB.close()
                self.passToNextLogic()
                
        if "OPEN" in logic:
            if "DOOR_A" in logic:
                self.doorA.open()
                self.passToNextLogic()
            if "DOOR_B" in logic:
                self.doorB.open()
                self.passToNextLogic()
        
        if "TARE" in logic:
            self.tare()            
            self.passToNextLogic()
                
        if "WAIT" in logic:
            if "DOOR_A" in logic:
                if self.doorA.isOrderDone():
                    self.passToNextLogic()
            if "DOOR_B" in logic:
                if self.doorB.isOrderDone():
                    self.passToNextLogic()
            if "SINGLE_ANIMAL" in logic:
                if len( self.weightList ) > 0:
                    if self.isWeightOfOneMouse( np.mean( self.weightList ) ): # use the last 10 measurement to pass
                        self.passToNextLogic()
            if "AT_LEAST_ONE_ANIMAL" in logic:
                if len( self.weightList ) > 0:
                    if self.isWeightAtLeastOneMouse( np.mean( self.weightList ) ): # use the last 10 measurement to pass
                        self.passToNextLogic()
            argument = logic.split()[1]
            if argument[-1]=="s":
                print("wait for logic started")
                self.setLogicProcess( WaitForSecondLogic( self, argument[:-1] ) ) #self.logicProcess = WaitForSecondLogic( self, argument[:-1] )
                
        if "CHECK_ONE_ANIMAL" in logic:
            self.setLogicProcess( CheckForOneAnimalLogic( self ) ) #self.logicProcess = CheckForOneAnimalLogic( self )
        
        if "CHECK_NO_ANIMAL" in logic:
            self.setLogicProcess( CheckNoAnimalLogic( self ) ) # self.logicProcess = CheckNoAnimalLogic( self )   
             
        if "CHECK_ANIMAL_ID_TOA" in logic:
            self.setLogicProcess( CheckAnimalIdLogic( self , "TO SIDE A") ) #self.logicProcess = CheckAnimalIdLogic( self , "TO SIDE A")
                
        if "CHECK_ANIMAL_ID_TOB" in logic:
            self.setLogicProcess( CheckAnimalIdLogic( self , "TO SIDE B") ) #self.logicProcess = CheckAnimalIdLogic( self , "TO SIDE B")
                    
        if "GOTO" in logic and not "ERRORGOTO" in logic:
            value = self.getGoto(logic)                              
            self.logicCursor = value
        
    def monitor(self):
        
        while( self.stopped == False ):            
            time.sleep( 0.1 )
            #time.sleep( 0.1 )            
                
            # gate logic            
            #self.lock.acquire()
            
            
            self.playLogic()
            
            #self.RFIDDetectionList.clear()
            
            if self.forcedRFIDDetection != None:
                if self.forcedRFIDDetection not in self.RFIDDetectionList: 
                    self.RFIDDetectionList.append( self.forcedRFIDDetection )
                
            '''
            #self.lock.release()
            # security logic for doors                        
            ms = time.time()*1000.0
            if ms-self.previousTime > 250: #1000
                chronoDoorLogic = datetime.now()
                #logging.info("monitor : Trying to acquire")
                #self.lock.acquire()
                self.doorA.performLogic() 
                self.doorB.performLogic()
                #self.lock.release()
                self.previousTime = ms
                timeInDoorLogic = ( datetime.now() - chronoDoorLogic ).total_seconds()
                #logging.info(f"time in door logic: {timeInDoorLogic} s" )
            '''
    
    def monitor2(self):
        while( self.stopped == False ):            
            time.sleep( 0.1 )
            
            #self.lock.release()
            # security logic for doors                        
            ms = time.time()*1000.0
            if ms-self.previousTime > 250: #1000
                chronoDoorLogic = datetime.now()
                #logging.info("monitor : Trying to acquire")
                #self.lock.acquire()
                self.doorA.performLogic() 
                self.doorB.performLogic()
                #self.lock.release()
                self.previousTime = ms
                timeInDoorLogic = ( datetime.now() - chronoDoorLogic ).total_seconds()
                #logging.info(f"time in door logic: {timeInDoorLogic} s" )
    
        
    def getPosition(self):
        print("Door A", self.doorA.motor.get_position() )
        print("Door B", self.doorB.motor.get_position() )
    
    def open(self):
        if self.stopped:
            logging.info("open error: The gate is in stopped state.")
            return
        
        self.doorA.open()
        self.doorB.open()
        
    def close(self):
        
        if self.stopped:
            logging.info("close error: The gate is in stopped state.")
            return

        self.doorA.close()            
        self.doorB.close()
    
    def getOrder(self):
        return self.order
    
    def checkSetOrderOptions(self, options , text ):
        for s in options:
            if s==text:
                return True
        return False 
    
    def setOrder (self, order, noOrderAtEnd=False, options=[] ):
        
        if self.stopped:
            logging.info("setOrder error: The gate is in stopped state.")
            return
    
        if self.antennaRFID !=None:
            self.antennaRFID.enableReading(False)

        logging.info( "Set order " + str( order ) )
        
                
        self.lock.acquire()
        
        self.logicProcess = None # protected by acquire
        self.order = order
        self.logicCursor = 0
        
        if self.order == GateOrder.NO_ORDER:            
            self.logicList= []
            
        if self.order == GateOrder.OPEN_CLOSE_HABITUATION:            
            self.logicList= []
            self.logicList.append( "OPEN DOOR_A" )
            self.logicList.append( "OPEN DOOR_B" )
            self.logicList.append( "WAIT 5s" )
            self.logicList.append( "CLOSE DOOR_A" )
            self.logicList.append( "CLOSE DOOR_B" )
            self.logicList.append( "WAIT 5s" )
        
        if self.order == GateOrder.TEST_RFID_GATE_MODE:
            self.logicList = []
            self.logicList.append( "START: LOG TEST_RFID_GATE_MODE STARTED" )
            self.logicList.append( "CHECK_ANIMAL_ID_TOB ERRORGOTO ERROR" )
            self.logicList.append( "LOG LOG TEST_RFID_GATE_MODE: RFID READ SUCCESS" )
            self.logicList.append( "GOTO START" )
            
            self.logicList.append( "ERROR: LOG TEST_RFID_GATE_MODE: DID NOT READ RFID" )
            self.logicList.append( "GOTO START" )
            
            
        if self.order == GateOrder.ALLOW_SINGLE_A_TO_B:            
            self.logicList = []
            self.logicList.append( "START: CLOSE DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "REOPEN_A: OPEN DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )            
            self.logicList.append( "WAIT SINGLE_ANIMAL" ) # with weight
            self.logicList.append( "CLOSE DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "CHECK_ONE_ANIMAL ERRORGOTO START" ) # with weight
            if self.rfidControlEnabled:
                self.logicList.append( "CHECK_ANIMAL_ID_TOB ERRORGOTO EMPTYA" )
            self.logicList.append( "LOG ALLOW_SINGLE_A_TO_B ANIMAL ACCEPTED" )
            self.logicList.append( "REOPEN_B:OPEN DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "EXITLOOP: CHECK_NO_ANIMAL ERRORGOTO EXITLOOP" )
            self.logicList.append( "CLOSE DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "CHECK_NO_ANIMAL ERRORGOTO REOPEN_B" )
            self.logicList.append( "TARE BALANCE" )
            self.logicList.append( "LOG ALLOW_SINGLE_A_TO_B DONE" )
            if ( noOrderAtEnd ):
                self.logicList.append( "SETORDER NO_ORDER" )
            else:
                self.logicList.append( "GOTO START" )
                
            #subs:
            self.logicList.append( "EMPTYA:OPEN DOOR_A" )
            self.logicList.append( "CHECK_NO_ANIMAL ERRORGOTO EMPTYA" )
            self.logicList.append( "GOTO REOPEN_A" )
            
        
        if self.order == GateOrder.ALLOW_SINGLE_B_TO_A:
            
            self.logicList = []
            self.logicList.append( "START: CLOSE DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "REOPEN_B: OPEN DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )            
            self.logicList.append( "WAIT SINGLE_ANIMAL" ) # with weight
            self.logicList.append( "CLOSE DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "CHECK_ONE_ANIMAL ERRORGOTO START" ) # with weight
            if self.rfidControlEnabled:
                self.logicList.append( "CHECK_ANIMAL_ID_TOA ERRORGOTO EMPTYB" )
            self.logicList.append( "LOG ALLOW_SINGLE_B_TO_A ANIMAL ACCEPTED" )
            self.logicList.append( "REOPEN_A:OPEN DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "EXITLOOP: CHECK_NO_ANIMAL ERRORGOTO EXITLOOP" )
            self.logicList.append( "CLOSE DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "CHECK_NO_ANIMAL ERRORGOTO REOPEN_A" )
            self.logicList.append( "TARE BALANCE" )
            self.logicList.append( "LOG ALLOW_SINGLE_B_TO_A DONE" )
            
            if ( noOrderAtEnd ):
                self.logicList.append( "SETORDER NO_ORDER" )
            else:
                self.logicList.append( "GOTO START" )

            #subs:
            self.logicList.append( "EMPTYB:OPEN DOOR_B" )
            self.logicList.append( "CHECK_NO_ANIMAL ERRORGOTO EMPTYB" )
            self.logicList.append( "GOTO REOPEN_B" )
            
        if self.order == GateOrder.ONLY_ONE_ANIMAL_IN_B:
            # the system waits for an animal coming from A.
            # then once the animal leave the gate in B, the gate waits for the animal to come back in A.
            
            self.logicList = []
            
            # the gate is waiting for an animal in area connected to A
            self.logicList.append( "START: CLOSE DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "REOPEN_A: OPEN DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )            
            self.logicList.append( "WAIT SINGLE_ANIMAL" ) # with weight
            self.logicList.append( "CLOSE DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "CHECK_ONE_ANIMAL ERRORGOTO START" ) # with weight
            if self.rfidControlEnabled:
                self.logicList.append( "CHECK_ANIMAL_ID_TOB ERRORGOTO EMPTYA" )
                            
            self.logicList.append( "LOG ANIMAL FREE TO GET TO SIDE B" ) # the gates to access A area is closed and the animal can only leave by B
            self.logicList.append( "REOPEN_B:OPEN DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "EXITLOOP1: CHECK_NO_ANIMAL ERRORGOTO EXITLOOP1" )
            
            '''
            if False: # close the door and reopen it immediately when animal reach side B
                self.logicList.append( "CLOSE DOOR_B" ) 
                self.logicList.append( "WAIT DOOR_B" )
            '''
            
            self.logicList.append( "CHECKOUTB:CHECK_NO_ANIMAL ERRORGOTO CHECKOUTB" ) # was: CHECK_NO_ANIMAL ERRORGOTO REOPEN_B 
            #self.logicList.append( "TARE BALANCE" )
            self.logicList.append( "LOG ANIMAL IS IN SIDE B" )
            self.logicList.append( "GOTO NEXT" )
            
            #subs:            
            self.logicList.append( "EMPTYA:OPEN DOOR_A" )
            self.logicList.append( "CHECK_NO_ANIMAL ERRORGOTO EMPTYA" )
            self.logicList.append( "GOTO REOPEN_A" )
            
            # system is waiting for animal in B area to get back to A.
            
            self.logicList.append( "NEXT:CLOSE DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "REOPEN_B2: OPEN DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )            
            self.logicList.append( "WAIT SINGLE_ANIMAL" ) # with weight
            self.logicList.append( "CLOSE DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "CHECK_ONE_ANIMAL ERRORGOTO NEXT" ) # with weight
            
            
            if self.checkSetOrderOptions( options, "no rfid check on return"):
                pass
            else:
                if self.rfidControlEnabled:
                    self.logicList.append( "CHECK_ANIMAL_ID_TOA ERRORGOTO EMPTYB" )
                
            self.logicList.append( "LOG ANIMAL FREE TO GET TO SIDE A" ) # the gates to access B area is closed and the animal can only leave by A
            self.logicList.append( "REOPEN_A2:OPEN DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "EXITLOOP2: CHECK_NO_ANIMAL ERRORGOTO EXITLOOP2" )
            
            if True:
                # close the door after the animal comes back in A
                self.logicList.append( "CLOSE DOOR_A" )
                self.logicList.append( "WAIT DOOR_A" )
                self.logicList.append( "CHECK_NO_ANIMAL ERRORGOTO REOPEN_A2" )
                self.logicList.append( "TARE BALANCE" )
            
            
            self.logicList.append( "LOG ANIMAL BACK IN SIDE A" )
            if ( noOrderAtEnd ):
                self.logicList.append( "SETORDER NO_ORDER" )
            else:
                self.logicList.append( "GOTO START" )
            
            #subs:
            self.logicList.append( "EMPTYB:OPEN DOOR_B" )
            self.logicList.append( "CHECK_NO_ANIMAL ERRORGOTO EMPTYB" )
            self.logicList.append( "GOTO REOPEN_B" )
            
        if self.order == GateOrder.ONLY_ONE_ANIMAL_IN_A:
            # the system waits for an animal coming from B.
            # then once the animal leave the gate in A, the gate waits for the animal to come back in B.
            
            self.logicList = []
            
            # the gate is waiting for an animal in area connected to B
            self.logicList.append( "START: CLOSE DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "REOPEN_B: OPEN DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )            
            self.logicList.append( "WAIT SINGLE_ANIMAL" ) # with weight
            self.logicList.append( "CLOSE DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "CHECK_ONE_ANIMAL ERRORGOTO START" ) # with weight
            if self.rfidControlEnabled:
                self.logicList.append( "CHECK_ANIMAL_ID_TOA ERRORGOTO EMPTYB" )
                            
            self.logicList.append( "LOG ANIMAL FREE TO GET TO SIDE A" ) # the gates to access B area is closed and the animal can only leave by A
            self.logicList.append( "REOPEN_A:OPEN DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "EXITLOOP1: CHECK_NO_ANIMAL ERRORGOTO EXITLOOP1" )
            
            
            
            self.logicList.append( "CHECKOUTA:CHECK_NO_ANIMAL ERRORGOTO CHECKOUTA" ) 
            #self.logicList.append( "TARE BALANCE" )
            self.logicList.append( "LOG ANIMAL IS IN SIDE A" )
            self.logicList.append( "GOTO NEXT" )
            
            #subs:            
            self.logicList.append( "EMPTYB:OPEN DOOR_B" )
            self.logicList.append( "CHECK_NO_ANIMAL ERRORGOTO EMPTYB" )
            self.logicList.append( "GOTO REOPEN_B" )
            
            # system is waiting for animal in A area to get back to B.
            
            self.logicList.append( "NEXT:CLOSE DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "REOPEN_A2: OPEN DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )            
            self.logicList.append( "WAIT SINGLE_ANIMAL" ) # with weight
            self.logicList.append( "CLOSE DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "CHECK_ONE_ANIMAL ERRORGOTO NEXT" ) # with weight
            
            
            if self.checkSetOrderOptions( options, "no rfid check on return"):
                pass
            else:
                if self.rfidControlEnabled:
                    self.logicList.append( "CHECK_ANIMAL_ID_TOB ERRORGOTO EMPTYA" )
                
            self.logicList.append( "LOG ANIMAL FREE TO GET TO SIDE B" ) # the gates to access A area is closed and the animal can only leave by B
            self.logicList.append( "REOPEN_B2:OPEN DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "EXITLOOP2: CHECK_NO_ANIMAL ERRORGOTO EXITLOOP2" )
            
            if True:
                # close the door after the animal comes back in B
                self.logicList.append( "CLOSE DOOR_B" )
                self.logicList.append( "WAIT DOOR_B" )
                self.logicList.append( "CHECK_NO_ANIMAL ERRORGOTO REOPEN_B2" )
                self.logicList.append( "TARE BALANCE" )
            
            
            self.logicList.append( "LOG ANIMAL BACK IN SIDE B" )
            if ( noOrderAtEnd ):
                self.logicList.append( "SETORDER NO_ORDER" )
            else:
                self.logicList.append( "GOTO START" )
            
            #subs:
            self.logicList.append( "EMPTYA:OPEN DOOR_A" )
            self.logicList.append( "CHECK_NO_ANIMAL ERRORGOTO EMPTYA" )
            self.logicList.append( "GOTO REOPEN_A" )


        if self.order == GateOrder.ALLOW_MULTIPLE_A_TO_B:            
            self.logicList = []
            self.logicList.append( "START: CLOSE DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "REOPEN_A: OPEN DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )            
            self.logicList.append( "WAIT AT_LEAST_ONE_ANIMAL" )
            self.logicList.append( "CLOSE DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "REOPEN_B:OPEN DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "EXITLOOP: CHECK_NO_ANIMAL ERRORGOTO EXITLOOP" )
            self.logicList.append( "CLOSE DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "CHECK_NO_ANIMAL ERRORGOTO REOPEN_B" )
            self.logicList.append( "TARE BALANCE" )
            self.logicList.append( "LOG ALLOW_MULTIPLE_A_TO_B DONE" )
            self.logicList.append( "GOTO START" )
            
        if self.order == GateOrder.ALLOW_MULTIPLE_B_TO_A:            
            self.logicList = []
            self.logicList.append( "START: CLOSE DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "REOPEN_B: OPEN DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )            
            self.logicList.append( "WAIT AT_LEAST_ONE_ANIMAL" )
            self.logicList.append( "CLOSE DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "REOPEN_A:OPEN DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "EXITLOOP: CHECK_NO_ANIMAL ERRORGOTO EXITLOOP" )
            self.logicList.append( "CLOSE DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "CHECK_NO_ANIMAL ERRORGOTO REOPEN_A" )
            self.logicList.append( "TARE BALANCE" )
            self.logicList.append( "LOG ALLOW_MULTIPLE_B_TO_A DONE" )
            self.logicList.append( "GOTO START" )
        
        if self.order == GateOrder.EMPTY_IN_A:
            
            self.logicList = []
            self.logicList.append( "REOPEN_A:OPEN DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "EXITLOOP: CHECK_NO_ANIMAL ERRORGOTO EXITLOOP" )
            self.logicList.append( "CLOSE DOOR_A" )
            self.logicList.append( "WAIT DOOR_A" )
            self.logicList.append( "CHECK_NO_ANIMAL ERRORGOTO REOPEN_A" )
            self.logicList.append( "TARE BALANCE" )
            self.logicList.append( "LOG EMPTY IN A DONE" )
            self.logicList.append( "SETORDER NO_ORDER" )
                            
        if self.order == GateOrder.EMPTY_IN_B:
            
            self.logicList = []
            self.logicList.append( "REOPEN_B:OPEN DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "EXITLOOP: CHECK_NO_ANIMAL ERRORGOTO EXITLOOP" )
            self.logicList.append( "CLOSE DOOR_B" )
            self.logicList.append( "WAIT DOOR_B" )
            self.logicList.append( "CHECK_NO_ANIMAL ERRORGOTO REOPEN_B" )
            self.logicList.append( "TARE BALANCE" )
            self.logicList.append( "LOG EMPTY IN B DONE" )
            self.logicList.append( "SETORDER NO_ORDER" )
                            
        self.checkLogic()
        self.lock.release()
        self.fireEvent( DeviceEvent( "gate" , self, "setOrder" , order ) )
    
    def setRFIDControlEnabled(self, b ):
        self.rfidControlEnabled = b
    
    def fireEvent(self, deviceEvent ):        
        for listener in self.deviceListenerList:
            listener( deviceEvent )
    
    def addDeviceListener(self , listener ):
        self.deviceListenerList.append( listener )
        
    def removeDeviceListener(self , listener ):
        self.deviceListenerList.remove( listener )
    
    def shutdown(self):        
        # shutsDown the gate
        
        logging.info("Stopping the gate")
        self.stopped = True
        # wait for the monitoring thread to quit
        time.sleep( 1 )
        
        try:
            if self.antennaRFID != None:
                self.antennaRFID.close()
                time.sleep(1.5) # to let the control thread finish
        except:
            logging.info("Can't shutdown RFIDs")
        
        try:    
            if self.arduino != None:
                self.arduino.close()
        except:
            logging.info("Can't shutdown Arduino")
            
        try:
            self.doorA.motor.disable_torque()
            self.doorB.motor.disable_torque()
        except:
            logging.info("Can't shutdown motors")
        
        try:            
            self.motorManager.close_port()
        except:
            logging.info("Can't shutdown motors' com port")
        
        logging.info("Gate shutdown done.")
    
            
        
        #Ax12.close_port()

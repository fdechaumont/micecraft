'''
Created on 23 sept. 2021

@author: Fab
'''

from dynamixel_sdk import * 
import logging
import traceback
import threading
from _datetime import datetime
from enum import Enum
from micecraft.soft.alarm.Alarm import Alarm, AlarmState

    
class MotorManager:
    # Manage Dynamixel AX12A
    # one Motor manager manage all motors on a given com port.
    
    '''
    PROTOCOL_VERSION = 1.0
    BAUDRATE = 1000000             # Dynamixel default baudrate    
    # Dynamixel will rotate between this value
    MIN_POS_VAL = 0
    MAX_POS_VAL = 1023
    
    ERROR = 1
    '''
    
    NB_MAX_COMMUNICATION_ATTEMPTS = 30

    
    def open_port(self):
        
        if self.portHandler.openPort():
            pass
            #logging.info("MotorManager: Succeeded to open the port")
        else:
            #logging.info("MotorManager: Failed to open the port. Quits.")            
            quit()
    
    
    def set_baudrate(self):
        if self.portHandler.setBaudRate(self.BAUDRATE):
            pass
            #logging.info("MotorManager: Succeeded to change the baudrate")
        else:
            #logging.info("MotorManager: Failed to change the baudrate")            
            quit()

    
    def close_port(self):
        # Close port
        self.portHandler.closePort()
        #print('Successfully closed port')

    def __init__(self, comPort ):
        
        self.alarm = Alarm( "Motor Manager" )
        self.nbAttemptsBeforeAlarm = 5
                
        self.comPort = comPort 
        self.PROTOCOL_VERSION = 1.0
        self.BAUDRATE = 1000000    # 115000        
        self.MIN_POS_VAL = 0
        self.MAX_POS_VAL = 1023
        print(f"MotorManager {comPort} step 1")
        self.portHandler = PortHandler(self.comPort )
        print(f"MotorManager {comPort} step 2")
        self.packetHandler = PacketHandler(self.PROTOCOL_VERSION)
        print(f"MotorManager {comPort} step 3")
        self.open_port()
        print(f"MotorManager {comPort} step 4")
        self.set_baudrate()
        print(f"MotorManager {comPort} step 5")

        self.motorThreadLock = threading.Lock()
        
        
    def check_error(self, comm_result, dxl_err , nbAttempts ):
        
        
        logError = False
        if nbAttempts > self.nbAttemptsBeforeAlarm:
            logError = True
            
        #print( comm_result )
        #traceback.print_exc()
        
        '''
        known error type:
        
        if the power is lost:
        Error (1) MotorManager: COM80: [TxRxResult] Incorrect status packet!
        
        if the usb cable is removed:
        Error (1) MotorManager: COM80: [TxRxResult] Port is in use!
        '''
        
        #logging.info("CHECK ERROR ------------------------------------------ ")
        
        if comm_result != COMM_SUCCESS:
            if logError:
                logging.info("-------------- MOTOR ERROR : Is the external power lost ? Is the usb cable disconnected ?")
                logging.info( datetime.now() )
                logging.info( threading.current_thread().name )
                logging.info( threading.get_ident() )
            
            if nbAttempts > self.nbAttemptsBeforeAlarm:
                self.alarm.sendAlarmMail( AlarmState.ALARM_ON , "Communication problem with motors.\nIs the external power lost ? Is the usb cable disconnected ? Number of attempts to control motor: {nbAttempt}" )
            
            '''
            for line in traceback.format_stack():
                logging.info(line.strip())
            '''
            if logError:
                logging.info( f"Error (1) MotorManager: {self.comPort}: {self.packetHandler.getTxRxResult(comm_result)}" )
                logging.info("--------------")            
            
        elif dxl_err != 0:
            
            # Error (2) MotorManager: COM80: [RxPacketError] Overheat error!
            
            errorText = self.packetHandler.getRxPacketError(dxl_err)
            
            if logError:
                logging.info( f"Error (2) MotorManager: {self.comPort}: {errorText}" )                
                logging.info("Is motor connected to power ?")
            
            # TMP test
            '''
            for line in traceback.format_stack():
                logging.info(line.strip())
            '''
            
            '''
            2023-07-12 08:54:03.751: Is motor connected to power ?
            2023-07-12 08:54:03.991: Error (2) MotorManager: COM10: [RxPacketError] Overload error! (Giuilio)
            
            testing here
            Error (2) MotorManager: COM31: [RxPacketError] Out of range error!
            '''
        
        if comm_result != COMM_SUCCESS:
            
            try:
                if logError:
                    logging.info("MotorManager : Trying to reconnect motors... (step 1 > closing port)")                
                time.sleep(1)
                try:
                    self.close_port()
                    time.sleep(1)
                except:
                    if logError:
                        logging.info("Motor manager: Cannot close port (port may be already lost or disconnected ?)")
                             
                self.PROTOCOL_VERSION = 1.0
                self.BAUDRATE = 1000000            
                self.MIN_POS_VAL = 0
                self.MAX_POS_VAL = 1023
                if logError:
                    logging.info("MotorManager : Trying to reconnect motors... (step 2 > port configuration)")
                self.portHandler = PortHandler(self.comPort )
                if logError:
                    logging.info("MotorManager : Trying to reconnect motors... (step 3 > setting up communication protocol)")
                self.packetHandler = PacketHandler(self.PROTOCOL_VERSION)
                if logError:
                    logging.info("MotorManager : Trying to reconnect motors... (step 3 > opening port)")
                self.open_port()
                if logError:
                    logging.info("MotorManager : Trying to reconnect motors... (step 4 > setting baudrate)")
                self.set_baudrate()
                if logError:
                    logging.info("MotorManager : Trying to reconnect motors... (step 5 > procedure done)")
                if self.alarm.state == AlarmState.ALARM_ON:
                    self.alarm.sendAlarmMail( AlarmState.ALARM_OFF , "Communication with motors recovered." )
                
            
            except Exception as e:
                logging.info(e)
            
            
            
        if comm_result != COMM_SUCCESS:
            time.sleep( 0.5 )
                
    
    
    
    
    
    

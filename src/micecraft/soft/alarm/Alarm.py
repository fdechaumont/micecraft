'''
Created on 2 juin 2023

@author: Fabrice de Chaumont
'''

import logging
from enum import Enum
from datetime import datetime, timedelta
from micecraft.soft.mail.Mail import Mail

class AlarmState(Enum):
    ALARM_ON = 1
    ALARM_OFF = 2    
    
class Alarm(object):    
    
    '''
    Manage alarms for MiceCraft
    '''
    
    # variables shared by all alarms:
    mails = []
    # use Alarm.experimentName='your experiment name' to set it once for all alarms. use capital for Alarm for static access
    experimentName ="no experiment name" 
    
    def __init__( self , alarmName , numberOfSecondsBetweenMail = 60*10 ):
        self.alarmName = alarmName
        logging.info("Creating alarm for " + str ( self.alarmName ) )
        self.alarmCount = 0
        self.state = AlarmState.ALARM_OFF
        self.lastMailDateTime = datetime.now()-timedelta(days=365)
        self.timeBetweenMailInS = numberOfSecondsBetweenMail
        
    def setTimeBetweenMailInS(self, nbSeconds ):
        self.timeBetweenMailInS = nbSeconds        
        
    def isAlarmOn( self ):
        return self.state == AlarmState.ALARM_ON        
    
    def checkIfMailShouldBeSent(self , alarmState ):
        
        # if we change state, then send the mail no matter time interval with previous one
        if self.state!= alarmState:
            return True
        
        # if the state and the command is off, don't send error
        if self.state == AlarmState.ALARM_OFF and alarmState == AlarmState.ALARM_OFF:
            return False
            
        secondSinceLastMail = abs(datetime.now()-self.lastMailDateTime).seconds
        if secondSinceLastMail > self.timeBetweenMailInS:
            return True
        
        return False
    
    def sendAlarmMail(self, alarmState, content, fileList = [] ):
        
        # check if a mail of alert has already been sent (to prevent spamming)
        try:
            sendMailOk = self.checkIfMailShouldBeSent( alarmState )
            self.state = alarmState
        
            subject = "["+str( self.state ).split(".")[1]+"] " + str( self.experimentName ) + " - " + str( self.alarmName ) + " - #" + str( self.alarmCount )
            
            if sendMailOk:
                logging.info(f"{self.alarmName} #{self.alarmCount}: {str(self.state)}")
            
            if content == None:
                content = subject
                    
            mail = Mail()                
            mail.sendAlert(self.mails, subject, content, fileList )
            self.lastMailDateTime = datetime.now()
            self.alarmCount+=1
        
        except Exception as e:
            logging.info(f"Exception in sendAlarmMail.")
            logging.info(e)
            
    
        
    
    
        
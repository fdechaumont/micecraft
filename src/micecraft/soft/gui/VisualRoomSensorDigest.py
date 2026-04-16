'''
Created on 11 juil. 2025

@author: fabri
'''


from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QApplication, QMenuBar, QMenu
from PyQt6.QtGui import QPaintEvent, QFont, QPen, QColor, QPainter
from PyQt6.QtCore import QRect, Qt
from PyQt6 import *



class VisualRoomSensorDigest(object):
        
    def draw( self, painter, textRect = QRect( 0, 100 , 100,100 ) ):
        
        if self.roomSensorDigest == None:
            return
        
        s=""
        for probe in self.probeList:
            value = self.roomSensorDigest.roomSensor.getValue(probe)
            
            if value != None:
                s+=f"{probe} : {value:.2f}\n"
        
        c = QtGui.QColor( 10,10,10)
                        
        painter.setBrush( c )
        painter.setPen(QtGui.QPen( c, 1))
        font = QFont('Times', 8)
        painter.setFont( font )
                    
        painter.drawText( textRect, Qt.AlignCenter, s )

        
        
    def __init__(self, roomSensorDigest ):
        
        self.probeList = [
            "Pressure",
            "Temperature",
            "Humidity",
            "r",
            "g",
            "b",
            "a",
            "Sound level",
            "Tilting x",
            "Tilting y",
            "Shock",
            "Raw accel x",
            "Raw accel y",
            "Raw accel z",
        ]
        
        self.roomSensorDigest = roomSensorDigest 
        
        
        
        #self.storageAlarm = Alarm( "Storage alarm", numberOfSecondsBetweenMail= 60*60*6 )
        
        
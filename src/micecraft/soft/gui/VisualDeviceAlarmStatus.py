'''
Created on 6 janv. 2025

@author: Fab
'''

from PyQt6 import QtCore
from PySide6.QtGui import Qt, QColor

from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QApplication, QMenuBar
from PyQt6.QtGui import QPaintEvent, QFont, QPen, QColor, QPainter
from PyQt6.QtCore import QRect

from PyQt6 import *

class VisualDeviceAlarmStatus(object):
        
    def draw( self, painter , device, ellipseRect = QRect( 45, 60,10,10 ), textRect = QRect( 0, 13 , 100,50 ), textInNormalState = "Ok"  ):
        
        # draw device health status (alarms)
        self.blink+=1
        if self.blink > 10:
            self.blink = 0
                
        #c = QtGui.QColor(100,100,100)
        c = QtGui.QColor(0,128,0)
        painter.setBrush( c )
        painter.setPen(QtGui.QPen( c, 1))
        painter.drawEllipse( ellipseRect )

        if device != None:
            alarm = device.isAlarmOn()
            if alarm != False:
                if self.blink > 5:
                    c = QtGui.QColor(255,25,25)
                    painter.setBrush( c )
                    painter.setPen(QtGui.QPen( c , 1))
                    painter.drawEllipse( ellipseRect )
                    font = QFont('Times', 8)                    
                    painter.setFont( font )
                    painter.drawText( textRect, Qt.AlignCenter, alarm )
            
            if alarm == False and textInNormalState != "":
                font = QFont('Times', 8)                    
                painter.setFont( font )
                painter.drawText( textRect, Qt.AlignCenter, textInNormalState )
                
        
    def __init__(self ):
        self.blink = 0
        
        

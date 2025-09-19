'''
Created on 6 janv. 2025

@author: Fab
'''

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import  QPainter, QPaintEvent, QColor, QFont
from PyQt5.Qt import QRect, QImage, QRegion, QLabel, QPushButton, QMenu

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
        
        

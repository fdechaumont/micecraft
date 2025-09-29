'''
Created on 14 mars 2023

@author: Fab
'''

from micecraft.soft.gui.VisualDeviceAlarmStatus import VisualDeviceAlarmStatus

from PyQt6 import QtCore
from PySide6.QtGui import Qt, QColor
from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QApplication, QMenuBar, QMenu
from PyQt6.QtGui import QPaintEvent, QFont, QPen, QColor, QPainter
from PyQt6.QtCore import QRect
from PyQt6 import *

class WLever(QWidget):

    def __init__(self, x , y , *args, **kwargs):
        super().__init__( *args, **kwargs)
        
        self.x = x*200+100
        self.y = y*200+100
        self.angle = 0
        self.setGeometry( int( self.x ), int ( self.y ), 100, 100)
        self.lever = None
        self.name= "lever"
        self.visualDeviceAlarmStatus = VisualDeviceAlarmStatus()
    
    def setAngle(self , angle ):
        self.angle = angle
        self.update()
    
    def setName(self, name ):
        self.name = name
    
    def contextMenuEvent(self, event):
       
        menu = QMenu(self)
        
        if self.lever != None:
            title = menu.addAction( f"{self.name} connected to {self.lever.comManager.comPort}" )
        else:
            title = menu.addAction( f"{self.name} (no device bound)" )
        title.setDisabled(True)
                
        leverPress = menu.addAction("Simulate lever press")
        leverRelease = menu.addAction("Simulate lever release")
        switchLight = menu.addAction("Switch light")
        
        if self.lever == None:
            leverPress.setDisabled( True )
            switchLight.setDisabled( True )
        
        action = menu.exec(  event.globalPos() )
        
        if action == leverPress:            
            self.lever.press()

        if action == leverRelease:
            self.lever.release()

        if action == switchLight:            
            self.lever.switchLight()
            
    def bindToLever(self , lever ):
        self.lever = lever
    
    def paintEvent(self, event: QPaintEvent):
        
        super().paintEvent( event )
        
        painter = QPainter()
        painter.begin(self)

        painter.translate(self.width()/2,self.height()/2);
        painter.rotate(self.angle);
        painter.translate(-self.width()/2,-self.height()/2);
                
        # block
        painter.fillRect( 25+0, 50 , 50 , 50, QColor( 150 , 150, 150 ))
        painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 4)) 
        painter.drawRect( 25+0, 50 , 50 , 50 )
        
        painter.fillRect( 25+10, 90 , 30 , 30, QColor( 220 , 100, 100))
        
        if self.lever != None:
            if self.lever.isLightOn():
                painter.fillRect( 25+0, 50 , 50 , 50, QColor( 255 , 255, 150 ))
            else:
                painter.fillRect( 25+0, 50 , 50 , 50, QColor( 50 , 50, 50 ))
            
        
        if self.lever != None:
            self.visualDeviceAlarmStatus.draw( painter, self.lever )
                
        font = QFont('Times', 10)
        font.setBold(True)
        painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 4))
        painter.setFont( font )
        painter.drawText( QRect( 0, 0 , 100,50 ), Qt.AlignCenter, self.name )
        
        painter.end()

    def mousePressEvent(self, event):
        self.__mousePressPos = None
        self.__mouseMovePos = None
        if event.button() == Qt.MouseButton.LeftButton:            
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()

        super(WLever, self).mousePressEvent(event)

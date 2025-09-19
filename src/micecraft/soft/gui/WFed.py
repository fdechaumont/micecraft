'''
Created on 14 mars 2023

@author: Fabrice de Chaumont
'''

from PyQt6.QtGui import QPaintEvent, QPainter, QFont, QPen, QColor
from PyQt6.QtCore import QRect, Qt
from PyQt6 import *
from PyQt6.QtWidgets import QWidget, QMenu

import logging

class WFed(QWidget):

    def __init__(self, x , y , *args, **kwargs):
        super().__init__( *args, **kwargs)
        
        self.x = x*200+100
        self.y = y*200+100
        self.angle = 0
        self.setGeometry( int( self.x ), int ( self.y ), 100, 100)
        
        self.name= "fed"
        self.fed = None
    
    def bindToFed(self , fed ):
        self.fed = fed
        
    def setAngle(self , angle ):
        self.angle = angle
        self.update()
    
    def setName(self, name ):
        self.name = name
        
    def contextMenuEvent(self, event):
       
        menu = QMenu(self)
        
        
        title = menu.addAction( self.name )
        title.setDisabled(True)
        
        
        deliver = menu.addAction("Deliver pellet")
        click = menu.addAction("Emit click")
        lightOn = menu.addAction("Lights on (full white)")
        lightOff = menu.addAction("Lights off")
        hello = menu.addAction("Send hello to the fed")
        
        menu.addSeparator()
        forceNosePokeLeft = menu.addAction("Force nose poke left")
        forceNosePokeRight = menu.addAction("Force nose poke right")
        
        menu.addSection("Orders")
        
        action = menu.exec(  event.globalPos() )
        if self.fed == None:
            print("No fed bound to this graphical component.")
            return
        
        if action == deliver:
            self.fed.feed()
        
        if action == click:
            self.fed.click()
            
        if action == lightOn:
            self.fed.light()
            
        if action == lightOff:
            self.fed.lightoff()
        
        if action == forceNosePokeLeft:
            self.fed.leftIn()
            
        if action == forceNosePokeRight:
            self.fed.rightIn()
            
        if action == hello:
            self.fed.hello()
       
    
    def paintEvent(self, event: QPaintEvent):
        
        
        super().paintEvent( event )
        
        painter = QPainter()
        painter.begin(self)
        
        painter.translate(self.width()/2,self.height()/2);
        painter.rotate(self.angle);
        painter.translate(-self.width()/2,-self.height()/2);
                
        # block
        painter.fillRect(0, int ( self.height()/2 ) , int ( self.width() ) , int ( self.height()/2 ), QColor(200, 200, 200))
        painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 4)) 
        painter.drawRect(0, int ( self.height()/2 ), int ( self.width() ), int ( self.height()/2 ) )
        
        # nose poke 1
        painter.fillRect( int ( 1*self.width()/6 ), int ( 3*self.height()/4 ), int ( self.width()/6 ), int ( self.height( ) ), QColor(100, 100, 100))
        # nose poke 2
        painter.fillRect( int ( 4*self.width()/6 ), int ( 3*self.height()/4 ), int ( self.width()/6 ), int ( self.height() ), QColor(100, 100, 100))
        # fed area
        
        painter.fillRect(int (self.width()/2-self.width()/7 ), int ( 5*self.height()/6 ), int ( self.width()/3.5 ), int ( self.height()/6 ) , QColor(50, 50, 50))
                        
        font = QFont('Times', 15 )
        font.setBold(True)
        painter.setFont( font )
        painter.drawText( QRect( 0, int( self.height()/2.5 ) , int ( self.width() ) , int ( self.height()/2) ), QtCore.Qt.AlignmentFlag.AlignCenter, self.name )
        
        # draw status
        painter.setPen(QtGui.QPen(QtGui.QColor( 10,10,10), 7)) # no status
        if self.fed != None:
            if self.fed.alarmConnect.isAlarmOn():
                painter.setPen(QtGui.QPen(QtGui.QColor(200,25,25), 7))
            else:
                painter.setPen(QtGui.QPen(QtGui.QColor(25,200,25), 7))
            
        painter.drawEllipse( 10,int( self.height()/2 )+10,10,10 )

        
        painter.end()

    def mousePressEvent(self, event):
        self.__mousePressPos = None
        self.__mouseMovePos = None
        if event.button() == Qt.MouseButton.LeftButton:
            self.__mousePressPos = event.globalPosition().toPoint()
            self.__mouseMovePos = event.globalPosition().toPoint()

        super(WFed, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            # adjust offset from clicked point to origin of widget
            currPos = self.mapToGlobal(self.pos())
            globalPos = event.globalPosition().toPoint()
            diff = globalPos - self.__mouseMovePos
            newPos = self.mapFromGlobal(currPos + diff)
            self.move(newPos)

            self.__mouseMovePos = globalPos

        super(WFed, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.__mousePressPos is not None:
            moved = event.globalPosition().toPoint() - self.__mousePressPos 
            if moved.manhattanLength() > 3:
                event.ignore()
                return

        super(WFed, self).mouseReleaseEvent(event)


'''
Created on 14 mars 2023

@author: Fabrice de Chaumont
'''
from PyQt6.QtGui import QPaintEvent, QPainter, QFont, QPen
from PyQt6.QtCore import QRect, Qt
from PyQt6 import *

import os
from micecraft.soft.gui.Wall import *
from PyQt6.QtWidgets import QWidget

os.environ["QT_ENABLE_HIGHDPI_SCALING"]   = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCALE_FACTOR"]             = "1"

class WBlock(QWidget):
    
    '''
    Widget Block
    '''

    def __init__(self, x,y, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        
        self.x = x*200+100
        self.y = y*200+100
        self.w = 200
        self.h = 200
        self.backgroundColor = QtGui.QColor( 220, 220, 220 )
        self.setGeometry( int( self.x ) , int ( self.y ) , self.w, self.h)
        self.name ="block"
        self.angle = 0
        self.wallList = []
        
        self.selected = False
        #self.setFocusPolicy( Qt.StrongFocus );
    
    def setSize(self ,w , h ):
        self.w = w
        self.h = h
        self.setGeometry( int( self.x ) , int ( self.y ) , self.w, self.h)
        
        
    def setName(self , name ):
        self.name = name
        self.update()
    
    def setAngle(self , angle ):
        self.angle = angle
        self.update()
        
    def addWall(self , wall ):
        self.wallList.append( wall )
        
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selected = True        
        
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.selected = False
        
    
    def keyPressEvent(self, event):

        if event.key() == QtCore.Qt.Key_R:
            self.angle+=90
            self.update()    
        event.accept()
        
    def setBackGroundColor(self , r=220, g=220, b=220 ):        
        self.backgroundColor = QtGui.QColor( r ,g , b )        
        
    def paintEvent(self, event: QPaintEvent):
        
        painter = QPainter()
        painter.begin(self)
            
        painter.translate(100,100);
        painter.rotate(self.angle);
        painter.translate(-100,-100);
        
        
        painter.fillRect(0, 0, self.w, self.h, self.backgroundColor)

        painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 2))         
        painter.drawRect(0,0,self.w,self.h)
        
        #painter.drawEllipse(0, 0, 40, 40)
        painter.setPen(QtGui.QPen(QtGui.QColor(200,200,200), 4))
        font = QFont('Times', 30)
        font.setBold(True)
        painter.setFont( font )
        if self.angle==180:
            painter.translate(100,100);
            painter.rotate(self.angle);
            painter.translate(-100,-100);
            
        painter.drawText( QRect( 0,0,self.w,int(self.h/2) ) , QtCore.Qt.AlignmentFlag.AlignCenter, self.name )

        #self.currentPhaseLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter) 

        if self.angle==180:
            painter.translate(100,100);
            painter.rotate(self.angle);
            painter.translate(-100,-100);
            
        # draw walls
        
        for wall in self.wallList:
            
                            
            painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 16 , Qt.PenStyle.SolidLine ))                
                
            if wall.type == WallType.GRID:                
                painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 16 , Qt.PenStyle.DashDotLine ))

            if wall.type == WallType.PLAIN or wall.type == WallType.GRID:
            
                if wall.side == WallSide.BOTTOM:
                    painter.drawLine( 0,self.h,self.w,self.h )
                if wall.side == WallSide.TOP:
                    painter.drawLine( 0,0,self.w,0 )
                if wall.side == WallSide.LEFT:
                    painter.drawLine( 0,0,0,self.h )
                if wall.side == WallSide.RIGHT:
                    painter.drawLine( self.w,0,self.w,self.h )
                    
            if wall.type == WallType.DOOR:
            
                if wall.side == WallSide.BOTTOM:
                    painter.drawLine( 0,200,100-25,200 )
                    painter.drawLine( 100+25,200,200,200 )
                if wall.side == WallSide.TOP:                                        
                    painter.drawLine( 0,0,100-25,0 )
                    painter.drawLine( 100+25,0,200,0 )
                if wall.side == WallSide.LEFT:
                    painter.drawLine( 0,0,0,100-25 )
                    painter.drawLine( 0,100+25,0,200 )
                if wall.side == WallSide.RIGHT:
                    painter.drawLine( 200,0,200,100-25 )
                    painter.drawLine( 200,100+25,200,200 )

        if self.selected:
            painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 2 , Qt.DotLine ))
            distance = 20
            painter.drawRect( 0+distance,0+distance,self.w-distance*2,self.h-distance*2 )
        
        painter.end()
        
        
    def mousePressEvent(self, event):
        self.__mousePressPos = None
        self.__mouseMovePos = None
        if event.button() == Qt.MouseButton.LeftButton:
            self.__mousePressPos = event.globalPosition().toPoint()
            self.__mouseMovePos = event.globalPosition().toPoint()

        super(WBlock, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        
        if event.buttons() == Qt.MouseButton.LeftButton:
            # adjust offset from clicked point to origin of widget
            currPos = self.mapToGlobal(self.pos())
            globalPos =  event.globalPosition().toPoint()
            diff = globalPos - self.__mouseMovePos
            newPos = self.mapFromGlobal(currPos + diff)
            self.move(newPos)

            self.__mouseMovePos = globalPos

        super(WBlock, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.__mousePressPos is not None:
            moved = event.globalPosition().toPoint() - self.__mousePressPos 
            if moved.manhattanLength() > 3:
                event.ignore()
                return

        super(WBlock, self).mouseReleaseEvent(event)

'''
Created on 14 mars 2023

@author: Fab
'''

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import  QPainter, QPaintEvent, QColor, QFont
from PyQt5.Qt import QRect, QImage, QRegion, QLabel, QPushButton

class WWMouse2(QtWidgets.QWidget):

    
    def __init__(self, x,y, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.x = x
        self.y = y
        
        self.setGeometry( int(self.x), int(self.y), 125, 50 )
        self.name ="block"
        self.rfid = None
        self.description = ""
        self.number = 0
        self.setBackgroundColor( 100, 100, 100 )
    
    def setName(self , name ):
        self.name = name
        self.update()
    
    def setAngle(self , angle ):
        self.angle = angle
        self.update()
        
    def setBackgroundColor(self , r , g , b  ):    
        self.backGroundColor = QtGui.QColor(r,g,b)

    def paintEvent(self, event: QPaintEvent):
        
        painter = QPainter()
        painter.begin(self)
            
        painter.fillRect(0, 0, 125, 50, self.backGroundColor )

        painter.setPen( QtGui.QPen(QtGui.QColor(100,100,100), 4) ) 
        painter.drawRect(0,0,125,50)
        
        painter.setPen(QtGui.QPen(QtGui.QColor(30,30,30), 4))
        font = QFont('Times', 10)
        font.setBold(True)
        painter.setFont( font )
        
        txt = self.rfid
        if txt==None:
            txt="No RFID"
        if self.description !="":
            txt+="\n"+self.description
        painter.drawText( QRect( 0,0,125,50) , Qt.AlignCenter, txt )

        painter.drawText( QRect( 5,5,20,10) , Qt.AlignCenter, str( self.number ) )

        #painter.drawText( QRect( 0,20,125,50) , Qt.AlignCenter, self.description )

        painter.end()
    
        
    def mousePressEvent(self, event):
        self.__mousePressPos = None
        self.__mouseMovePos = None
        if event.button() == QtCore.Qt.LeftButton:
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()

        super(WWMouse2, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            # adjust offset from clicked point to origin of widget
            currPos = self.mapToGlobal(self.pos())
            globalPos = event.globalPos()
            diff = globalPos - self.__mouseMovePos
            newPos = self.mapFromGlobal(currPos + diff)
            self.move(newPos)

            self.__mouseMovePos = globalPos

        super(WWMouse2, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.__mousePressPos is not None:
            moved = event.globalPos() - self.__mousePressPos 
            if moved.manhattanLength() > 3:
                event.ignore()
                return

        super(WWMouse2, self).mouseReleaseEvent(event)

'''
Created on 14 mars 2023

@author: Fab
'''

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import  QPainter, QPaintEvent, QColor, QFont
from PyQt5.Qt import QRect, QImage, QRegion, QLabel, QPushButton

class WWMouse(QtWidgets.QWidget):

    
    def __init__(self, x,y, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.x = x*200+100
        self.y = y*200+100
        
        self.setGeometry( int(self.x), int(self.y), 100, 100)
        self.name ="block"
        self.angle = 0
        self.img = QImage()
        self.img.load("mouse.jpg")
        
        mask = QRegion( 0,0,100,100, QRegion.Ellipse)
        self.setMask( mask )
        
        
        
        #self.keyPressed.connect(self.on_key)
    
    def setName(self , name ):
        self.name = name
        self.update()
    
    def setAngle(self , angle ):
        self.angle = angle
        self.update()


    
    
    def paintEvent(self, event: QPaintEvent):
        
        painter = QPainter()
        painter.begin(self)
            
        painter.translate(self.width()/2,self.height()/2);
        painter.rotate(self.angle);
        painter.translate(-self.width()/2,-self.height()/2);
        
        painter.drawImage(self.rect(), self.img)
        
        painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 4))
        painter.drawEllipse(0, 0, self.width(), self.height())
        
        '''
        painter.fillRect(0, 0, 200, 200, QColor(220, 220, 220))

        painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 4)) 
        painter.drawRect(0,0,200,200)
        
        #painter.drawEllipse(0, 0, 40, 40)
        painter.setPen(QtGui.QPen(QtGui.QColor(200,200,200), 4))
        font = QFont('Times', 30)
        font.setBold(True)
        painter.setFont( font )
        painter.drawText( QRect( 0,0,200,50) , Qt.AlignCenter, self.name )
        '''

        painter.end()
    
        
    def mousePressEvent(self, event):
        self.__mousePressPos = None
        self.__mouseMovePos = None
        if event.button() == QtCore.Qt.LeftButton:
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()

        super(WWMouse, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            # adjust offset from clicked point to origin of widget
            currPos = self.mapToGlobal(self.pos())
            globalPos = event.globalPos()
            diff = globalPos - self.__mouseMovePos
            newPos = self.mapFromGlobal(currPos + diff)
            self.move(newPos)

            self.__mouseMovePos = globalPos

        super(WWMouse, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.__mousePressPos is not None:
            moved = event.globalPos() - self.__mousePressPos 
            if moved.manhattanLength() > 3:
                event.ignore()
                return

        super(WWMouse, self).mouseReleaseEvent(event)

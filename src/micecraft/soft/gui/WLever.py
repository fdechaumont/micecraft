'''
Created on 14 mars 2023

@author: Fab
'''
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import  QPainter, QPaintEvent, QColor, QFont
from PyQt5.Qt import QRect, QImage, QRegion, QLabel, QPushButton, QMenu
from visualexperiments.Block import Block

from visualexperiments.VisualDeviceAlarmStatus import VisualDeviceAlarmStatus

class WWWLever(QtWidgets.QWidget):

    def __init__(self, x , y , *args, **kwargs):
        super().__init__( *args, **kwargs)
        
        self.x = x*200+100
        self.y = y*200+100
        self.angle = 0
        self.setGeometry( int( self.x ), int ( self.y ), 100, 100)
        self.lever = None
        self.name= "lever\ntest"
        self.visualDeviceAlarmStatus = VisualDeviceAlarmStatus()


        '''        
        layout = QtWidgets.QVBoxLayout()
        title = QLabel( "Fed" , objectName="balanceTitle" )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget( title )
        self.balanceWidget = MplCanvas (self, width=5, height=3 )        
        self.balanceWidget.axes.plot([0,1,2,3,4], [10,1,20,3,40])
        self.balanceAx = self.balanceWidget.axes        
        self.balanceAx.set_ylabel("weight (g)")
        plt.tight_layout()
        layout.addWidget( self.balanceWidget )
        tareButton= QPushButton("Force tare balance")
        layout.addWidget( tareButton )
        tareButton.clicked.connect( self.tare )
        layout.addStretch()        
        self.setLayout(layout)
        '''
    
    '''
    def tare(self):
        print( "tare")
        self.balanceAx.clear()
        
        a = []
        b = []
        for i in range(10):
            a.append( randint(0,40) )
            b.append( randint(0,40) )
            
        self.balanceWidget.axes.plot(a,b)
        self.balanceWidget.fig.canvas.draw()
    ''' 
    
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
        
        #menu.addSection("Actions")

        
        leverPress = menu.addAction("Simulate lever press")
        leverRelease = menu.addAction("Simulate lever release")
        switchLight = menu.addAction("Switch light")
        
        if self.lever == None:
            leverPress.setDisabled( True )
            switchLight.setDisabled( True )
        
        action = menu.exec_(self.mapToGlobal(event.pos()))
        
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
        
        #painter.drawRect( 0, 0 , 200 , 200 )
        
        painter.fillRect( 25+10, 90 , 30 , 30, QColor( 220 , 100, 100))
        
        if self.lever != None:
            if self.lever.isLightOn():
                painter.fillRect( 25+0, 50 , 50 , 50, QColor( 255 , 255, 150 ))
            else:
                painter.fillRect( 25+0, 50 , 50 , 50, QColor( 50 , 50, 50 ))
            
        
        if self.lever != None:
            self.visualDeviceAlarmStatus.draw( painter, self.lever )
        
        
        '''
        # draw device health status (alarms)
        c = QtGui.QColor(100,100,100)
        painter.setBrush( c )
        painter.setPen(QtGui.QPen( c, 1))
        painter.drawEllipse( 45, 60,10,10 )

        if self.lever != None:
            alarm = self.lever.isAlarmOn()
            if alarm != False:
                if self.blink > 5:
                    c = QtGui.QColor(255,25,25)
                    painter.setBrush( c )
                    painter.setPen(QtGui.QPen( c , 1))
                    painter.drawEllipse( 45, 60,10,10 )
                    font = QFont('Times', 8)                    
                    painter.setFont( font )
                    painter.drawText( QRect( 0, 13 , 100,50 ), Qt.AlignCenter, alarm )
        '''
        

        
        
        # trigger
        #painter.fillRect(int ( self.width()/8 ), 0 , int ( self.width()/4 ) , 100, QColor(0, 255, 0 ))
        # int ( self.height()/3 )
        '''
        # nose poke 1
        painter.fillRect( int ( 1*self.width()/6 ), int ( 3*self.height()/4 ), int ( self.width()/6 ), int ( self.height( ) ), QColor(100, 100, 100))
        # nose poke 2
        painter.fillRect( int ( 4*self.width()/6 ), int ( 3*self.height()/4 ), int ( self.width()/6 ), int ( self.height() ), QColor(100, 100, 100))
        # fed area
        
        painter.fillRect(int (self.width()/2-self.width()/7 ), int ( 5*self.height()/6 ), int ( self.width()/3.5 ), int ( self.height()/6 ) , QColor(50, 200, 50))
        '''
        
                
        font = QFont('Times', 10)
        font.setBold(True)
        painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 4))
        painter.setFont( font )
        painter.drawText( QRect( 0, 0 , 100,50 ), Qt.AlignCenter, self.name )
        
        painter.end()

    def mousePressEvent(self, event):
        self.__mousePressPos = None
        self.__mouseMovePos = None
        if event.button() == QtCore.Qt.LeftButton:
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()

        super(WWWLever, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            # adjust offset from clicked point to origin of widget
            currPos = self.mapToGlobal(self.pos())
            globalPos = event.globalPos()
            diff = globalPos - self.__mouseMovePos
            newPos = self.mapFromGlobal(currPos + diff)
            self.move(newPos)

            self.__mouseMovePos = globalPos

        super(WWWLever, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.__mousePressPos is not None:
            moved = event.globalPos() - self.__mousePressPos 
            if moved.manhattanLength() > 3:
                event.ignore()
                return

        super(WWWLever, self).mouseReleaseEvent(event)


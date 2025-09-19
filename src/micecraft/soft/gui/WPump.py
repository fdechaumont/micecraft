'''
Created on 14 mars 2023

@author: Fab
'''
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import  QPainter, QPaintEvent, QColor, QFont
from PyQt5.Qt import QRect, QImage, QRegion, QLabel, QPushButton, QMenu

from time import sleep
from micecraft.soft.gui.VisualDeviceAlarmStatus import VisualDeviceAlarmStatus




class WWWPump(QtWidgets.QWidget):

    def __init__(self, x , y , *args, **kwargs):
        super().__init__( *args, **kwargs)
        
        self.x = x*200+100
        self.y = y*200+100
        self.angle = 0
        self.setGeometry( int( self.x ), int ( self.y ), 100, 100)
        
        self.name= "pump\ntest"
        self.pump = None
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
    
    def paintEvent(self, event: QPaintEvent):
        
        
        super().paintEvent( event )
        
        painter = QPainter()
        painter.begin(self)

        #painter.drawRect( 0, 0 , self.width()-1 , self.height()-1 )
        
        painter.translate(self.width()/2,self.height()/2);
        painter.rotate(self.angle);
        painter.translate(-self.width()/2,-self.height()/2);
                
        # block
        w = 30
                    
        
        painter.fillRect( 10, 50 , w , 50, QColor( 150 , 150, 250 ))
        
        if self.pump != None:
            if self.pump.isLightOn():
                painter.fillRect( 10, 50 , w , 50, QColor( 255 , 255, 150 ))
        
        painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 4)) 
        painter.drawRect( 10, 50 , w , 50 )
        
        '''
        if self.pump.isLightOn():
            painter.fillRect( 15, 90 , w , 30, QColor( 100 , 100, 250 ))
        painter.fillRect( 15, 90 , w , 30, QColor( 255 , 255, 100 ))
        else:
        '''

        
        #painter.drawRect( 0, 0 , 200 , 200 )
        
        #painter.fillRect( 75+10, 90 , 30 , 30, QColor( 220 , 100, 100))
        w = 20
        painter.fillRect( 15, 90 , w , 30, QColor( 100 , 100, 250 ))
            
        
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
        painter.setFont( font )
        painter.drawText( QRect( 0, 0 , 50,50 ), Qt.AlignCenter, self.name )
        
        if self.pump != None:
            self.visualDeviceAlarmStatus.draw( painter, self.pump,
                                               ellipseRect = QRect( 22, 60,10,10 ), textRect = QRect( -25, 13 , 100,50 )  )
                
        painter.end()

    
    
    def contextMenuEvent(self, event):
       
        
        menu = QMenu(self)
        
        
        title = menu.addAction( self.name )
        title.setDisabled(True)
        
        
        drop = menu.addAction("Provide one drop")
        prime = menu.addAction("Prime pump")
        empty = menu.addAction("Pump water out of recipient (flush)")
        dropAndFlush = menu.addAction("10x drop and flush")
        menu.addSeparator()
        refill = menu.addAction("Set the water level to 'full refill'")
        actionLightOn = menu.addAction("Light On")
        actionLightOff = menu.addAction("Light Off")
        menu.addSeparator()
        simulateRewardPickedAction = menu.addAction("Simulate reward picked")
        
        action = menu.exec_(self.mapToGlobal(event.pos()))
        
        if self.pump == None:
            print("No action as there is no hardware device bound to this component")
            return 
        
        if action == drop:
            self.pump.deliverDrop(1)
        if action == prime:
            self.pump.prime()
        if action == empty:
            self.pump.flush( 255 , 1000 )
        if action == dropAndFlush:
            
            for n in range(10):
                n+=1
                '''
                pwm = 255
                duration = 20
                #s = "hello\n"
                s = f"pump,{int(pwm)},{int(duration)}\n"
                self.pump.send( s )
                '''
                self.pump.deliverDrop(1)
                #print( s, n  )
                #pump.pump( 255, 20 )
                sleep(0.1)
                s = f"flush,255,100\n"
                self.pump.send( s )
                print( s, n  )
                sleep(0.1)
            
        if action == refill:
            self.pump.refillLiquidLevel()
        if action == actionLightOn:
            self.pump.lightOn()            
        if action == actionLightOff:
            self.pump.lightOff()
        if action == simulateRewardPickedAction:
            self.pump._rewardPicked()
        
    def bindToPump(self , pump ):
        self.pump = pump

    
    def mousePressEvent(self, event):
        self.__mousePressPos = None
        self.__mouseMovePos = None
        if event.button() == QtCore.Qt.LeftButton:
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()

        super(WWWPump, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            # adjust offset from clicked point to origin of widget
            currPos = self.mapToGlobal(self.pos())
            globalPos = event.globalPos()
            diff = globalPos - self.__mouseMovePos
            newPos = self.mapFromGlobal(currPos + diff)
            self.move(newPos)

            self.__mouseMovePos = globalPos

        super(WWWPump, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.__mousePressPos is not None:
            moved = event.globalPos() - self.__mousePressPos 
            if moved.manhattanLength() > 3:
                event.ignore()
                return

        super(WWWPump, self).mouseReleaseEvent(event)
    


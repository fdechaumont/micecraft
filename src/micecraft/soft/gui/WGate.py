'''
Created on 14 mars 2023

@author: Fab
'''

'''
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import  QPainter, QPaintEvent, QColor, QFont
from PyQt5.Qt import QRect, QImage, QRegion, QLabel, QPushButton, QMenu
'''
from PyQt6.QtGui import QPaintEvent, QPainter, QFont, QPen
from PyQt6.QtCore import QRect, Qt
from PyQt6 import *

import logging
from visualexperiments.VisualDeviceAlarmStatus import VisualDeviceAlarmStatus

StyleSheet = '''

#button {
    text-align: center;
    font-size: 10pt;
    font-family: Arial;
    font-weight:bold;
    background-color:lightgray;
}

'''
class WWGate(Block):
    
    def __init__(self, x,y, *args, **kwargs ):
        
        super().__init__( x, y , *args, **kwargs )
        self.name ="GATE"    
        self.gate = None
        self.G_OpenPercentageA = 0
        self.G_OpenPercentageB = 0
        
        self.G_LidarExtA = False
        self.G_LidarInA = False
        self.G_LidarExtB = False
        self.G_LidarInB = False
        self.G_enableLidar = False
        self.G_CurrentOrder = None
        
        self.G_JamAOpen = 0
        self.G_JamAClose = 0
        self.G_JamBOpen = 0
        self.G_JamBClose = 0
        
        self.visualDeviceArduinoAlarmStatus = VisualDeviceAlarmStatus(  )
        self.visualDeviceRFIDAlarmStatus = VisualDeviceAlarmStatus(  )
        
        
            
        if self.gate != None:
            antenna = self.gate.antennaRFID
            if antenna != None:
                x = 75+10
                y = 120
                self.visualDeviceRFIDAlarmStatus.d
        
        '''
        self.setStyleSheet(StyleSheet)
        self.tareButton = QPushButton("Tare" , self , objectName="button"  )
        self.tareButton.clicked.connect( self.tareScale )
        if self.angle==90 or self.angle==180:
            self.tareButton.setGeometry( 10,100,55,20)
        else:
            self.tareButton.setGeometry( 70,150,55,20)
        '''
        
        '''
        self.refresher = QtCore.pyqtSignal()
        self.refresher.connect(self.on_refresh_data)
        thread = threading.Thread( target=self.monitorGateGUI , name = f"Thread VisualGate - {name}")
        #self.data_downloaded = QtCore.pyqtSignal(object)
        thread.start()
        time.sleep(1)
        '''
    
    def contextMenuEvent(self, event):
       
        menu = QMenu(self)
        
        title = menu.addAction( self.name )
        title.setDisabled(True)
        #menu.addSection("Actions")
        
        openA = menu.addAction("Open A")
        closeA = menu.addAction("Close A")
        openB = menu.addAction("Open B")
        closeB = menu.addAction("Close B")
        tareZero = menu.addAction("Tare to zero")
        
        # tare with animal menu --------------- start
        subMenu = menu.addMenu( "Tare with animal(s) in gate (scale shift)" )
        actionScaleWithAnimalDic= {}        
                    
        for i in range( 1 , 11 ):
            plural = "s"
            
            if i == 1:
                plural=""
            gr = round ( self.gate.mouseAverageWeight * i , 2 ) 
            item = subMenu.addAction( f"{i} animal{plural} in gate ({gr} grams)" )
            actionScaleWithAnimalDic[item] = gr
        # tare with animal menu --------------- end    
            
        menu.addSeparator()
        
        actionDic = {}
        for order in GateOrder:            
            item = menu.addAction( str(order) )
            actionDic[item] = order
        
        menu.addSeparator()
        
        '''
        visualCueAction = menu.addAction("Visual cues")
        visualCueAction.setCheckable( True )        
        if self.experiment.visualCueEnabled:
            visualCueAction.setChecked( True )
        '''
            
        forceScaleDisabled = menu.addAction("Use real scale value (normal mode)")
        forceScaleDisabled.setCheckable( True )
        if self.gate!=None:
            if self.gate.forcedWeightValue == None:
                forceScaleDisabled.setChecked( True )
        
        forceScale0 = menu.addAction("Force reading scale to 0 grams")
        forceScale0.setCheckable( True )
        if self.gate != None:
            if self.gate.forcedWeightValue == 0:
                forceScale0.setChecked( True )
            
        forceScaleCorrectAnimalWeight = menu.addAction("Force reading scale to expected animal weight")
        forceScaleCorrectAnimalWeight.setCheckable( True )
        if self.gate !=None:
            if self.gate.forcedWeightValue == self.gate.mouseAverageWeight:
                forceScaleCorrectAnimalWeight.setChecked( True )
        
            
        
        menu.addSeparator()
        
        forceRFIDDisabled = menu.addAction("No test RFID ID (normal mode)")
        forceRFIDDisabled.setCheckable( True )
        if self.gate != None:
            if self.gate.forcedRFIDDetection == None:
                forceRFIDDisabled.setChecked( True )
                
        forceRFID1 = menu.addAction("Force RFID reading 0001")
        forceRFID1.setCheckable( True )
        if self.gate != None:
            if self.gate.forcedRFIDDetection == "0001":
                forceRFID1.setChecked( True )
        
        forceRFID2 = menu.addAction("Force RFID reading 0002")
        forceRFID2.setCheckable( True )
        
        if self.gate != None:
            if self.gate.forcedRFIDDetection == "0002":
                forceRFID2.setChecked( True )
        
        forceRFID3 = menu.addAction("Force RFID reading 0003")
        forceRFID3.setCheckable( True )
        
        if self.gate != None:
            if self.gate.forcedRFIDDetection == "0003":
                forceRFID3.setChecked( True )
        
        forceRFID4 = menu.addAction("Force RFID reading 0004")
        forceRFID4.setCheckable( True )
        
        if self.gate != None:
            if self.gate.forcedRFIDDetection == "0004":
                forceRFID4.setChecked( True )
        
        
        action = menu.exec_(self.mapToGlobal(event.pos()))
        
        if self.gate == None:
            print("Can't perform action: no gate linked to this visual component.")
            return
        
        
        if action in actionScaleWithAnimalDic:
            self.gate.setScaleShift( actionScaleWithAnimalDic[action] )
        
        if action == openA:
            self.gate.doorA.open()
            logging.info(f"wwgate *{self.name}* user action: door a open.")
        if action == openB:
            self.gate.doorB.open()
            logging.info(f"wwgate *{self.name}* user action: door b open.")
        if action == closeA:
            self.gate.doorA.close()
            logging.info(f"wwgate *{self.name}* user action: door a close.")
        if action == closeB:
            self.gate.doorB.close()
            logging.info(f"wwgate *{self.name}* user action: door b close.")
        if action == tareZero:
            logging.info(f"wwgate *{self.name}* user action: tare.")
            self.gate.tare()
        if action in actionDic:        
            self.gate.setOrder( actionDic[action] )
            logging.info(f"wwgate *{self.name}* user set action: *{actionDic[action]}*.")
            
        if action == forceScale0:
            self.gate.forceWeightValue( 0 )
            
        if action == forceScaleCorrectAnimalWeight:
            self.gate.forceWeightValue( self.gate.mouseAverageWeight )
            
        if action == forceScaleDisabled:
            self.gate.disableForcedWeightValue()
            
        if action == forceRFID1:
            self.gate.forceRFIDDetection( "0001")
        
        if action == forceRFID2:
            self.gate.forceRFIDDetection( "0002")
        
        if action == forceRFID3:
            self.gate.forceRFIDDetection( "0003")
            
        if action == forceRFID4:
            self.gate.forceRFIDDetection( "0004")
            
        if action == forceRFIDDisabled:
            self.gate.disableForcedRFIDDetection()
        
        
    def checkAngle180(self, painter ):
        if self.angle == 180:
            painter.translate(100,100);
            painter.rotate(self.angle);
            painter.translate(-100,-100);

    def drawTextRotated(self , painter, rect, txt ):
        painter.save()
        painter.translate( rect.center )
        painter.rotate( 45 )
        painter.translate( -rect.center )
        painter.drawText( txt )
        painter.load()
    '''
    void CustomLabel::paintEvent(QPaintEvent* e)    
    {
    QPainter painter(this);

    painter.translate(m_rect.center());
    painter.rotate(m_rotation);
    painter.translate(-m_rect.center());
    painter.drawText(m_rect, Qt::AlignHCenter | Qt::AlignVCenter, m_text);

    QWidget::paintEvent(e);
    }    
    '''
    
    def drawArrowToA(self , painter ):
        painter.drawLine(50+10,100,150,100)
        painter.drawLine(50   ,100,50+10,100+10)
        painter.drawLine(50   ,100,50+10,100-10)
    
        
    def drawArrowToB(self , painter ):
        painter.drawLine(50,100,140,100)
        painter.drawLine(150   ,100,150-10,100+10)
        painter.drawLine(150   ,100,150-10,100-10)
    
    def paintEvent(self, event: QPaintEvent):
        
        super().paintEvent( event )
        
        painter = QPainter()
        painter.begin(self)

        painter.translate(100,100);
        painter.rotate(self.angle);
        painter.translate(-100,-100);
        
        # tunnel
        painter.fillRect(0, 100-25, 200, 50, QColor(240, 240, 240))        
        painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 4))
        
        '''
        try:
            if self.gate.isWeightOfOneMouse( self.G_CurrentWeight ):
                painter.fillRect(0, 100-25, 200, 50, QColor(193, 225, 193))
            if self.G_CurrentWeight < self.gate.mouseAverageWeight /4:
                painter.fillRect(0, 100-25, 200, 50, QColor( 174, 214, 241 ))
        except:
            pass
        '''
        
        
        painter.drawRect(0, 100-25,200, 50)
        
        # arrow if an order exists

        if self.gate != None:
            order = str( self.G_CurrentOrder )
            
            if "ALLOW_SINGLE_A_TO_B" in order:
                painter.setPen(QtGui.QPen(QtGui.QColor(200,200,200), 15 ))
                self.drawArrowToB( painter )
                
            if "EMPTY_IN_B" in order:
                painter.setPen(QtGui.QPen(QtGui.QColor(200,10,10), 15 ))
                self.drawArrowToB( painter )
                                
            
            if "ALLOW_SINGLE_B_TO_A" in order:
                painter.setPen(QtGui.QPen(QtGui.QColor(200,200,200), 15 ))
                self.drawArrowToA( painter )
                

            if "EMPTY_IN_A" in order:
                painter.setPen(QtGui.QPen(QtGui.QColor(200,10,10), 15 ))
                self.drawArrowToA( painter )
                
            if "ONLY_ONE_ANIMAL_IN_B" in order:
                logic = self.gate.getLogic()
                if logic != None:
                    if "EXITLOOP1: CHECK_NO_ANIMAL ERRORGOTO EXITLOOP1" in logic:
                        painter.setPen(QtGui.QPen(QtGui.QColor(200,200,200), 15 ))
                        self.drawArrowToB( painter )        
                    
                    if "EXITLOOP2: CHECK_NO_ANIMAL ERRORGOTO EXITLOOP2" in logic:
                        painter.setPen(QtGui.QPen(QtGui.QColor(200,200,200), 15 ))
                        self.drawArrowToA( painter )
                
            if "ONLY_ONE_ANIMAL_IN_A" in order:
                logic = self.gate.getLogic()
                if logic != None:
                    if "EXITLOOP1: CHECK_NO_ANIMAL ERRORGOTO EXITLOOP1" in logic:
                        painter.setPen(QtGui.QPen(QtGui.QColor(200,200,200), 15 ))
                        self.drawArrowToA( painter )        
                    
                    if "EXITLOOP2: CHECK_NO_ANIMAL ERRORGOTO EXITLOOP2" in logic:
                        painter.setPen(QtGui.QPen(QtGui.QColor(200,200,200), 15 ))
                        self.drawArrowToB( painter )
                
            
        
        # door A
        openPercentA = 0
        if self.gate != None:
            openPercentA = self.G_OpenPercentageA 
        painter.fillRect(QRect(20, int(openPercentA/2+100-25), 10, 50), QColor(255, 165, 0))
        painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 1)) 
        painter.drawRect(QRect(20, int(openPercentA/2+100-25), 10, 50))
        
        # lidar A
        if self.G_enableLidar:
            if self.G_LidarExtA: 
                painter.fillRect( QRect(10, 100-25-20, 10, 10), QColor(255, 10, 0))
            else:
                painter.fillRect( QRect(10, 100-25-20, 10, 10), QColor(10, 10, 10))
                
            if self.G_LidarInA:
                painter.fillRect( QRect(30, 100-25-20, 10, 10), QColor(255, 10, 0))
            else:
                painter.fillRect( QRect(30, 100-25-20, 10, 10), QColor(10, 10, 0))
        
        # jam A
        if self.angle==180:
            self.checkAngle180( painter )
            painter.drawText( QRect( 120,5,80,30) , Qt.AlignCenter, f"jam open/close:\n{self.G_JamAOpen} / {self.G_JamAClose}" )
            self.checkAngle180( painter )
        else:
            painter.drawText( QRect( 10,0,80,30) , Qt.AlignCenter, f"jam open/close:\n{self.G_JamAOpen} / {self.G_JamAClose}" )
        
        # door B
        openPercentB = 0
        if self.gate != None:
            openPercentB = self.G_OpenPercentageB
        painter.fillRect( QRect( 160, int(openPercentB/2+100-25), 10, 50), QColor(255, 165, 0))
        painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 1)) 
        painter.drawRect( QRect(160, int(openPercentB/2+100-25), 10, 50) )
        
        # lidar B
        if self.G_enableLidar:
            if self.G_LidarExtB: 
                painter.fillRect( QRect(170, 100-25-20, 10, 10), QColor(255, 10, 0))
            else:
                painter.fillRect( QRect(170, 100-25-20, 10, 10), QColor(10, 10, 10))
                
            if self.G_LidarInB:
                painter.fillRect( QRect(150, 100-25-20, 10, 10), QColor(255, 10, 0))
            else:
                painter.fillRect( QRect(150, 100-25-20, 10, 10), QColor(10, 10, 0))
                
        # jam B
        if self.angle==180:
            self.checkAngle180( painter )
            painter.drawText( QRect( 10,5,80,30) , Qt.AlignCenter, f"jam open/close:\n{self.G_JamBOpen} / {self.G_JamBClose}" )
            self.checkAngle180( painter )
        else:
            painter.drawText( QRect( 110,0,80,30) , Qt.AlignCenter, f"jam open/close:\n{self.G_JamBOpen} / {self.G_JamBClose}" )
        
        
        # draw A & B letters
        painter.setPen(QtGui.QPen(QtGui.QColor(255,255,255), 4))
        font = QFont('Times', 30)
        font.setBold(True)
        painter.setFont( font )
        
        if self.angle == 180:
            self.checkAngle180( painter )
            painter.drawText( QRect( 150,125,50,75), Qt.AlignCenter, "A" )
            painter.drawText( QRect( 10,125,50,75) , Qt.AlignCenter, "B" )
            self.checkAngle180( painter )
        else:
            painter.drawText( QRect( 0,125,50,75) , Qt.AlignCenter, "A" )
            painter.drawText( QRect( 140,125,50,75) , Qt.AlignCenter, "B" )
            
    
        if self.gate != None:
            
            self.updateGateInfo()
            
            '''
            painter.translate(100,100);
            painter.rotate(-self.angle);
            painter.translate(-100,-100);
            '''
            
            # display weight
            painter.setPen(QtGui.QPen(QtGui.QColor( 20, 20, 20), 4))
            font = QFont('Times', 10)
            painter.setFont( font )
            self.checkAngle180( painter )
            painter.drawText( QRect( 0,75,200,50) , Qt.AlignCenter, f"{str(round(self.G_CurrentWeight,2))} g [{int(self.gate.mouseAverageWeight * (1-self.gate.weightWindowFactor))}g/{int(self.gate.mouseAverageWeight * (1+self.gate.weightWindowFactor))}g]" )

            if self.gate.scaleShift!=0:
                painter.setPen(QtGui.QPen(QtGui.QColor( 255, 25, 25), 4))
                painter.drawText( QRect( 0,75+10,200,50+10) , Qt.AlignCenter, f"SCALE SHIFT ACTIVE: +{self.gate.scaleShift} g" )

            self.checkAngle180( painter )
                            
            
            
            # display current order and rfid read status
            order = str( self.G_CurrentOrder )
            if order != None:
                if "." in order:
                    order = order.split(".")[-1]
            self.checkAngle180( painter )
            painter.setPen(QtGui.QPen(QtGui.QColor( 20, 20, 20), 4))
            painter.drawText( QRect( 0,15,200,50) , Qt.AlignCenter, f"{order}" )

            if self.gate.rfidControlEnabled:
                if self.gate.antennaRFID.enabled:
                    painter.drawText( QRect( 0,140,200,50) , Qt.AlignCenter, f"Reading RFID" )
                    
            self.checkAngle180( painter )
                    
            
        if self.gate != None:
            arduino = self.gate.arduino
            x = 75-20
            y = 120
            self.checkAngle180( painter )
            self.visualDeviceArduinoAlarmStatus.draw( painter, arduino, ellipseRect = QRect( 22+x, 60+y,10,10 ), textRect = QRect( -25+x, 13+y , 100,50 ), textInNormalState="Scale/Lidar" )
            self.checkAngle180( painter )
            
        if self.gate != None:
            antenna = self.gate.antennaRFID
            if antenna != None:
                x = 75+20
                y = 120
                self.checkAngle180( painter )
                self.visualDeviceRFIDAlarmStatus.draw( painter, antenna, ellipseRect = QRect( 22+x, 60+y,10,10 ), textRect = QRect( -25+x, 13+y , 100,50 ), textInNormalState="RFID"  )
                self.checkAngle180( painter )
        # draw action
        
        '''
        font = QFont('Times', 8)
        font.setBold(True)
        painter.setFont( font )
        x=10
        y=30
        painter.fillRect( x, y, 50, 20, QColor(100, 100, 100))
        painter.setPen(QtGui.QPen(QtGui.QColor( 200, 200, 200), 4))
        painter.drawText( QRect( x,y,50,20) , Qt.AlignCenter, "Tare" )
        ''' 
        
        
        #print( Block.blockList )
        
        '''
        if ( self.orientation == WWOrientation.LEFT or self.orientation == WWOrientation.RIGHT ):             
            
        if ( self.orientation == WWOrientation.TOP or self.orientation == WWOrientation.BOTTOM ):             
            painter.fillRect(0, 100-25, 200, 50, QColor(240, 240, 240))
            painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100), 4)) 
            painter.drawRect(0, 100-25,200, 50)
        '''

        
        '''
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
        
    def gateListener(self , event ):
        
        #print( event )
        # count jam
        
        # jam log example:
        # 2023-02-01 12:20:58.187: [door B sugar gate] DoorStatus.JAMMED_CLOSEreason: LIDAR
        # 2023-02-01 12:20:58.203: [door B sugar gate] DoorStatus.JAMMED_CLOSE
        # 2023-02-01 12:27:20.871: [door B social gate] DoorStatus.JAMMED_OPEN

        if "door A" in event.description:
            if "JAMMED_OPEN" in event.description:
                self.G_JamAOpen += 1
            if "JAMMED_CLOSE" in event.description and not "LIDAR" in event.description:
                self.G_JamAClose += 1
                
        if "door B" in event.description:
            if "JAMMED_OPEN" in event.description:
                self.G_JamBOpen += 1
            if "JAMMED_CLOSE" in event.description and not "LIDAR" in event.description:
                self.G_JamBClose += 1
            
        
    def bindToGate(self , gate ):
        self.gate = gate
        self.gate.addDeviceListener( self.gateListener )
        self.gate.doorA.addDeviceListener( self.gateListener )
        self.gate.doorB.addDeviceListener( self.gateListener )        
        print("Binding gate and door" + str( self.gate ) )
    
    def tareScale(self):
        self.gate.tare()
    
    
    def updateGateInfo(self):
        
        self.gate.lock.acquire()
        self.G_CurrentWeight = self.gate.currentWeight
        self.G_CurrentOrder = self.gate.getOrder()
        
        self.G_OpenPercentageA = int( self.gate.doorA.cacheOpenPercentage )
        self.G_OpenPercentageB = int( self.gate.doorB.cacheOpenPercentage )
        #print( self.name + " " + str( self.G_OpenPercentageB ) )

        self.G_LidarExtA = self.gate.doorA.getLidarExt( )
        self.G_LidarInA = self.gate.doorA.getLidarIn( )
        self.G_LidarExtB = self.gate.doorB.getLidarExt( )
        self.G_LidarInB = self.gate.doorB.getLidarIn( )
        self.G_enableLidar = self.gate.enableLIDAR
        
        '''
        self.titleLabel.setText( self.gate.name )
        self.orderLabel.setText( str( self.gate.order ) )
        
        self.wDoorA.progressBar.setValue( int( self.gate.doorA.cacheOpenPercentage ) )
        self.wDoorA.orderLabel.setText( str( self.gate.doorA.doorOrder ) )
        self.wDoorA.statusLabel.setText( str( self.gate.doorA.status ) )
        
        self.wDoorB.progressBar.setValue( int ( self.gate.doorB.cacheOpenPercentage ) )
        self.wDoorB.orderLabel.setText( str( self.gate.doorB.doorOrder ) )
        self.wDoorB.statusLabel.setText( str ( self.gate.doorB.status ) )
        
        self.wBalance.setMeasures( self.gate.weightList, self.gate.mouseAverageWeight )
        
        #self.speed.setValue( self.gate.doorA.speedLimit )
        
        for r in self.RFIDDetectionList:                
            self.rfid.addRFID( r )
        self.RFIDDetectionList.clear()
                        
        self.wLogic.setLogic( self.gate.logicList , self.gate.logicCursor )
        
        # lidar reading
        detectionStyle = "QLabel { padding:10px; qproperty-alignment: AlignCenter; background-color: orange; }"
        noDetectionStyle = "QLabel { padding:10px; qproperty-alignment: AlignCenter; background-color: lightgreen; }"

        
        '''
        

        self.gate.lock.release()
        
'''
Created on 24 juin 2024

@author: Fabrice de Chaumont
'''

import threading
import time
import traceback
import sys

from micecraft.devices.lever.Lever import Lever
from micecraft.soft.gui.Wall import Wall, WallSide, WallType
from micecraft.soft.gui.WLever import WLever
from micecraft.soft.gui.WBlock import WBlock
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6 import QtCore
from PyQt6.QtGui import QPainter, QPaintEvent
from micecraft.soft.gui.WGate import WGate
from PyQt6.QtCore import Qt

class WVisualExperimentGateInGUI(QWidget):
    
    refresher = QtCore.pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shuttingDown = False
        
        print("Starting visual experiment...")
                
    def shutdown(self):
        
        print("Exiting...")
        self.shuttingDown = True
        
        print("Done.")
        
    
    def on_refresh_data(self):
        
        self.update()
    
    def monitorGUI(self):
        
        while( self.shuttingDown == False ):            
    
            self.refresher.emit()            
            time.sleep( 0.1 )      
            
    def listener(self , event ):
        print ( f"Event received: {event}" )
            
    def start(self ):
        
        # Definition of the visual elements
        
        block = WBlock( 0,0 , self )
        block.setName("Box A")
        block.addWall( Wall ( WallSide.RIGHT, wallType = WallType.DOOR ) )
        block.addWall( Wall ( WallSide.BOTTOM  ) )
        block.addWall( Wall ( WallSide.TOP ) )
        block.addWall( Wall ( WallSide.LEFT ) )
        
        block = WBlock( 2,0 , self )
        block.setName("Box B")
        block.addWall( Wall ( WallSide.RIGHT ) )
        block.addWall( Wall ( WallSide.BOTTOM ) )
        block.addWall( Wall ( WallSide.TOP ) )
        block.addWall( Wall ( WallSide.LEFT, wallType = WallType.DOOR ) )

        gate = WGate( 1 , 0 , self )
        
        self.resize(800,400)
        self.setWindowTitle( "MiceCraft - Gate display test" )
                
        self.thread = threading.Thread( target=self.monitorGUI )
        self.refresher.connect(self.on_refresh_data)
        self.thread.start()

        # the following show trick is needed if an input (the console) as taken the focus before, else the window will not show        
        self.setWindowFlag( Qt.WindowType.WindowStaysOnTopHint, True);
        self.show( )
        self.setWindowFlag( Qt.WindowType.WindowStaysOnTopHint, False);
        self.show( )

    
    def paintEvent(self, event: QPaintEvent):
                
        super().paintEvent( event )
        painter = QPainter()        
        painter.begin(self)
        # here should be located your custom display code
        
        painter.end()
    
def excepthook(type_, value, traceback_):
        traceback.print_exception(type_, value, traceback_)
        QtCore.qFatal('')

    
if __name__ == "__main__":
    
    sys.excepthook = excepthook
    
    def exitHandler():        
        visualExperiment.shutdown()
        
    
    app = QApplication([])
    
    app.aboutToQuit.connect(exitHandler)
    visualExperiment = WVisualExperimentGateInGUI()
    visualExperiment.start()
    
        
    sys.exit( app.exec() )
        

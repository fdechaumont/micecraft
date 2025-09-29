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


class WVisualExperiment(QWidget):
    
    refresher = QtCore.pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shuttingDown = False
        
        print("Starting visual experiment...")
                
    def shutdown(self):
        
        print("Exiting...")
        self.shuttingDown = True
        self.lever.shutdown()
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
        block.setName("Box")
        block.addWall( Wall ( WallSide.RIGHT ) )
        block.addWall( Wall ( WallSide.BOTTOM, wallType = WallType.GRID ) )
        block.addWall( Wall ( WallSide.TOP ) )
        block.addWall( Wall ( WallSide.LEFT, wallType = WallType.DOOR ) )
        
        self.lever = Lever( "COM23" ) # Create a lever
        visualLever = WLever( 0.25,-0.3, self ) # Create the visual lever widget
        visualLever.setName("Lever")
        visualLever.bindToLever( self.lever ) # Bind visual lever to device so that it can read its state.
        
        self.lever.addDeviceListener( self.listener )
        
        self.resize(400,400)
        self.setWindowTitle( "MiceCraft - Lever display test" )
                
        self.thread = threading.Thread( target=self.monitorGUI )
        self.refresher.connect(self.on_refresh_data)
        self.thread.start()
    
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
    visualExperiment = WVisualExperiment()
    visualExperiment.start()
    visualExperiment.show()
        
    sys.exit( app.exec() )
        

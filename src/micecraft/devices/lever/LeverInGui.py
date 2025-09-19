'''
Created on 24 juin 2024

@author: Fab
'''


from PyQt5 import QtCore, QtWidgets


import threading
import time
import traceback
import sys




class WWVisualExperiment(QtWidgets.QWidget):
    
    refresher = QtCore.pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.name ="Visual experiment monitoring"
        self.shuttingDown = False
        
        self.RFIDCurrentlyInB = None
        
        print("hello")
                
    def shutdown(self):
        print("Exiting...")
        self.shuttingDown=True
        self.lever.shutdown()
        
    
    def on_refresh_data(self):
        
        self.update()
    
    def monitorGUI(self):
        
        while( self.shuttingDown == False ):            
    
            self.refresher.emit()            
            time.sleep( 0.1 )      
            
    def listener(self , event ):
        print ( f"Event received: {event}" )
        
    
    def start(self ):
               
        block = Block( 0,0 , self )
        block.setName("Box")
        block.addWall( WWWall ( WWWallSide.RIGHT ) )
        block.addWall( WWWall ( WWWallSide.BOTTOM, wallType = WWWallType.GRID ) )
        block.addWall( WWWall ( WWWallSide.TOP ) )
        block.addWall( WWWall ( WWWallSide.LEFT, wallType = WWWallType.DOOR ) )
        
        self.lever = Lever( "COM23" )
        visualLever = WWWLever( 0.25,-0.3, self )
        visualLever.setName("Lever")
        visualLever.bindToLever( self.lever )
        
        self.lever.addDeviceListener( self.listener )
        
        self.resize(400,400)
        self.setWindowTitle( "LMT blocks - lever display test" )
                
        self.thread = threading.Thread( target=self.monitorGUI )
        self.refresher.connect(self.on_refresh_data)
        self.thread.start()
    
    def paintEvent(self, event: QPaintEvent):
        
        
        super().paintEvent( event )
        painter = QPainter()
        painter.setRenderHint(QPainter.Antialiasing);
        
        painter.begin(self)
        
        
        painter.end()
    
def excepthook(type_, value, traceback_):
        traceback.print_exception(type_, value, traceback_)
        QtCore.qFatal('')

    
if __name__ == "__main__":
    
    sys.excepthook = excepthook
    
    def exitHandler():
        visualExperiment.shutdown()
        
    
    app = QtWidgets.QApplication([])
    
    app.aboutToQuit.connect(exitHandler)
    visualExperiment = WWVisualExperiment()
    visualExperiment.start()
    visualExperiment.show()
    
    
    sys.exit( app.exec_() )
    
    print("ok")

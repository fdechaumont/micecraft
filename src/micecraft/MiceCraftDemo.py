'''
Created on 9 sept. 2025

@author: Fabrice de Chaumont
'''
import sys
import traceback
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication
from micecraft.examples.GateInGui import WVisualExperimentGateInGUI
from PyQt6.QtWidgets import QApplication, QWidget









def excepthook(type_, value, traceback_):
        traceback.print_exception(type_, value, traceback_)
        QtCore.qFatal('')


class MiceCraftDemo(object):
    
    '''
    Launch the demos
    '''

    def __init__(self ):
    
        '''
        Constructor
        '''
        print("MiceCraft demo started.")
        print("1: Show the gate graphical user interface")
        
        a = input("Select demo number:")
        
        
        if "1" in a:
            
            # start gate in GUI demo.
            
            sys.excepthook = excepthook
    
            
            def exitHandler():        
                visualExperiment.shutdown()
            
                
            
            app = QApplication( [] )
            
            app.aboutToQuit.connect(exitHandler)
            visualExperiment = WVisualExperimentGateInGUI()
            visualExperiment.start()
                
                    
            sys.exit( app.exec() )
        
        
if __name__ == "__main__":
    
    MiceCraftDemo()
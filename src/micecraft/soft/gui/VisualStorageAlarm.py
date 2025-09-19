'''
Created on 6 janv. 2025

@author: Fab
'''

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import  QPainter, QPaintEvent, QColor, QFont
from PyQt5.Qt import QRect, QImage, QRegion, QLabel, QPushButton, QMenu

     
import shutil



class VisualStorageAlarm(object):
        
    def draw( self, painter, textRect = QRect( 0, 100 , 100,100 ) ):
        
        
        
        total, used, free = shutil.disk_usage("/")
        total = round( total // (2**30), 2 )
        used = round( used // (2**30), 2 )
        free = round( free // (2**30), 2 )
        
        s = f"Total: {total} GB\nUsed: {used} GB\nFree: {free} GB\nMin: {self.minGB} GB"
        
        c = QtGui.QColor(0,128,0)
        if free < self.minGB:
            c = QtGui.QColor(255,0,0)
                        
        painter.setBrush( c )
        painter.setPen(QtGui.QPen( c, 1))
        font = QFont('Times', 8)
        painter.setFont( font )
                    
        painter.drawText( textRect, Qt.AlignCenter, s )

        
        
    def __init__(self, minGB=100 ):
        self.minGB = minGB
        self.storageAlarm = Alarm( "Storage alarm", numberOfSecondsBetweenMail= 60*60*6 )
        
        

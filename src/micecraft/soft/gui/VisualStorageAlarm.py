'''
Created on 6 janv. 2025

@author: Fab
'''

from PyQt6 import QtCore

from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QApplication, QMenuBar
from PyQt6.QtGui import QPaintEvent, QFont, QPen, QColor, QPainter
from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QPaintEvent, QPainter, QFont, QPen, QColor
     
import shutil
from micecraft.soft.alarm.Alarm import Alarm


class VisualStorageAlarm(object):
        
    def draw( self, painter, textRect = QRect( 0, 100 , 100,100 ) ):
        
        
        
        total, used, free = shutil.disk_usage("/")
        total = round( total // (2**30), 2 )
        used = round( used // (2**30), 2 )
        free = round( free // (2**30), 2 )
        
        s = f"Total: {total} GB\nUsed: {used} GB\nFree: {free} GB\nMin: {self.minGB} GB"
        
        
        c = QColor(0,128,0)
        if free < self.minGB:
            c = QColor(255,0,0)
                        
        painter.setBrush( c )
        painter.setPen( QPen( c, 1))
        font = QFont('Times', 8)
        painter.setFont( font )
                    
        painter.drawText( textRect, Qt.AlignCenter, s )

        
        
    def __init__(self, minGB=100 ):
        self.minGB = minGB
        self.storageAlarm = Alarm( "Storage alarm", numberOfSecondsBetweenMail= 60*60*6 )
        
        

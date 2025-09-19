'''
Created on 14 mars 2023

@author: Fabrice de Chaumont
'''

from enum import Enum

class WallSide( Enum ):
    TOP = 1
    BOTTOM= 2
    LEFT = 3
    RIGHT = 4

class WallType( Enum ):
    PLAIN = 1
    DOOR = 2
    GRID = 3    

    
class Wall:
    
    def __init__(self , wallSide : WallSide, wallType = WallType.PLAIN ):
        self.side = wallSide
        self.type = wallType
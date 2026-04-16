'''
Created on 13 mars 2025

@author: Fab
'''


import logging
import json
import os.path
import traceback

class ParameterSaver(object):
    '''
    This class is dedicated to save parameters an restore them when 
    the experiment is launched or/and relaunched several times
    
    for instance, it is useful to store current RFID in the system and associated parameters
    such as current progresses in tests
    '''


    def __init__(self, workingFolder, experimentName ):
        
        if logging.getLogger().hasHandlers():
            logging.info("Starting ParameterSaver")
        self.experimentName = experimentName
        self.jsonFileName = f"{workingFolder}/{self.experimentName}_ParameterSaver.json"
        print( self.jsonFileName )
        self.data = {}
        self._load()
        
    def _load(self ):
        if os.path.isfile( self.jsonFileName ):
            with open( self.jsonFileName ) as file:
                self.data = json.load( file )
                print( self.data )
            
    def save(self):
        print( "ParameterSaver save " + self.jsonFileName )
        try:
            json.dump( self.data, open( self.jsonFileName, 'w' ), indent = 4 )
        except:
            logging.info("Parameter saver can't save file.")
            logging.info( traceback.format_exc() )
            print(traceback.format_exc())
            
    def setData(self, data ):
        self.data = data
        self.save()
    
    def getData(self):
        return self.data
    
    def getValue(self , key ):
        if key not in self.data:
            return None
        return self.data[key]
    
    def setValue(self , key, value ):
        self.data[key] = value
        self.save()
        
        
        
        
        
        
        
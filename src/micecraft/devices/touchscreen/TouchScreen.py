'''
Created on 4 oct. 2023

@author: Fab
'''

import serial
from random import randint
import threading
import logging

from time import sleep

import random

import sys
from micecraft.soft.com_manager.ComManager import ComManager
from micecraft.soft.device_event.DeviceEvent import DeviceEvent
from micecraft.devices.touchscreen.inPy.GrassHopper import GrassHopper
from micecraft.devices.touchscreen.ThreadTest import ThreadTest



class TouchScreen(object):
    
    '''
    notes:
    
    - The TTL levels of the raspberry UART are at 3.3v
    - Win 11 compatibility: PROLIFIC PL2303GC chip
    
    #todo: ajouter offset x calib ecran et y et multi
    
    
    
    '''
    
    
    
    def __init__(self, comPort , name="TouchScreen" ):
        
        self.lock = threading.Lock()
        self.comPort = comPort
        self.name = name
        #self.connect()
        
        self.enabled = True
        self.deviceListenerList = []
        
        
        #self.communicationThread = threading.Thread(target=self.communication , name = f"TouchScreen Thread - {self.comPort}")
        #self.communicationThread.start()
        
        self.currentDisplay = {}
        self.transparency = 255
        
        self.comManager = ComManager( comPort, self.comListener, "touchscreen com", 115200 )
        self.comManager.enablePing()
        sleep(0.5) # fixme with a check if connected
        
        self.comManager.send( "config 3 1 350")
        self.displayCalibration = False
        
        
    def comListener(self, event ):
        
        if not self.enabled:
            return
        
        serialString = event.description
     
     
        
        # symbol touched id 2 at 3,1
        if "symbol touched" in serialString:
            
            ok = False
            
            
            try:
                data = serialString.split(" ")
                id = int( data[3] )
                where = data[-1]
                w = where.split(",")
                x = int( w[0] )
                y = int( w[1] )                        
                xf = int( w[2] )
                yf = int( w[3] )
                ok = True
            except:
                self.log( f"symbol touched : error in parse data: {serialString}")                    

            if ok:
                self.fireEvent( DeviceEvent( "touchscreen", self, serialString, ( id, x, y, xf, yf ) ) )
            

        if "symbol xy touched" in serialString:
            ok = False
            try:
                data = serialString.split(" ")
                name = data[3]
                id = int( data[5] )
                where = data[-1]
                w = where.split(",")
                x = int( float(w[0]) )
                y = int( float(w[1]) )                        
                xf = int( float(w[2]) )
                yf = int( float(w[3]) )
                ok = True
            except:
                self.log( f"symbol xy touched : error in parse data: {serialString}")
            
            if ok:         
                self.fireEvent( DeviceEvent( "touchscreen", self, serialString, ( name, id, x, y, xf, yf ) ) )
            
        if "missed" in serialString:
            ok = False
            try:
                
                # missed 640,497
                data = serialString.split(" ")
                where = data[-1]
                w = where.split(",")
                xf = int( w[0] )
                yf = int( w[1] )
                ok = True
            except:
                self.log( f"missed : error in parse data: {serialString}")
                
            if ok:                        
                self.fireEvent( DeviceEvent( "touchscreen", self, serialString, ( xf, yf ) ) )
            
        if "traceback" in serialString:
            self.fireEvent( DeviceEvent( "touchscreen", self, serialString ) )
        
          
        
    '''
    def connect(self):
        try:
            self.ser = serial.Serial( self.comPort,baudrate=115200 , timeout=None )
            

        except:
            self.log("Can't connect to com port")
    '''
    
    '''
    def communication(self):
        
        # init
        self.send( f"config 3 1 350" )
        self.displayCalibration = False

        while self.enabled:
            
            try:
                if self.ser.in_waiting > 0:
                    
                    line = self.ser.readline()
                    try:
                        serialString = line.decode("utf-8")
                    except Exception as e:                        
                        logging.info(f"[TouchScreen] Error in utf-8 decode {e}")
                                
                    
                    serialString = serialString.strip()
                
                    #print(f"** {serialString}")
                
                    # symbol touched id 2 at 3,1
                    if "symbol touched" in serialString:
                        
                        ok = False
                        try:
                            data = serialString.split(" ")
                            id = int( data[3] )
                            where = data[-1]
                            w = where.split(",")
                            x = int( w[0] )
                            y = int( w[1] )                        
                            xf = int( w[2] )
                            yf = int( w[3] )
                            ok = True
                        except:
                            self.log( f"symbol touched : error in parse data: {serialString}")                    

                        if ok:
                            self.fireEvent( DeviceEvent( "touchscreen", self, serialString, ( id, x, y, xf, yf ) ) )
                        

                    if "symbol xy touched" in serialString:
                        ok = False
                        try:
                            data = serialString.split(" ")
                            name = data[3]
                            id = int( data[5] )
                            where = data[-1]
                            w = where.split(",")
                            x = int( float(w[0]) )
                            y = int( float(w[1]) )                        
                            xf = int( float(w[2]) )
                            yf = int( float(w[3]) )
                            ok = True
                        except:
                            self.log( f"symbol xy touched : error in parse data: {serialString}")
                        
                        if ok:         
                            self.fireEvent( DeviceEvent( "touchscreen", self, serialString, ( name, id, x, y, xf, yf ) ) )
                        
                    if "missed" in serialString:
                        ok = False
                        try:
                            
                            # missed 640,497
                            data = serialString.split(" ")
                            where = data[-1]
                            w = where.split(",")
                            xf = int( w[0] )
                            yf = int( w[1] )
                            ok = True
                        except:
                            self.log( f"missed : error in parse data: {serialString}")
                            
                        if ok:                        
                            self.fireEvent( DeviceEvent( "touchscreen", self, serialString, ( xf, yf ) ) )
                        
                    if "traceback" in serialString:
                        self.fireEvent( DeviceEvent( "touchscreen", self, serialString ) )
                    
            except serial.SerialException:
                self.log("Error in serial. Disconnected ?")
                self.ser.close()                
                
                self.connect()
                #print("test")
                sleep( 1 )
            
            sleep( 0.005 )
                
                    
        logging.info(f"Shutting down touchscreen {self}")
        self.ser.close()
    '''

    def crash(self ):
        # force a crash (exception) on the device to test traceback report
        self.send( f"crash")
        
    def setConfig(self, nbCols, nbRows, imageSize ):
        #config 3 2 350
        self.nbCols = nbCols
        self.nbRows = nbRows
        self.imageSize = imageSize
        self.send( f"config {nbCols} {nbRows} {imageSize}" )
        
    def setTransparency (self , transparency ):
        transparency = int ( transparency * 255 )
        if transparency >= 0 and transparency <=255:
            self.transparency= transparency
            self.send( f"transparency {self.transparency}")
        
        
    def setYOffset(self , yOffset ):
        self.yOffset = yOffset
        self.send( f"yOffset {yOffset}")
            
    def setMouseMode(self ):
        # the ir screen is rotated to match the screen viewport
        self.send( f"mouseMode")
        
    

    def setRatMode(self ):
        # the ir screen is rotated to match the screen viewport
        self.send( f"ratMode")
        
    def setNormalMode(self ):
        # no screen rotation
        self.send( f"normalMode") 
        
    def ping(self):
        self.send( "ping" )
        
    def clear(self):
        # clear all images
        self.send("clear")
        self.log( "touchscreen clear" )
        self.currentDisplay.clear()
        
    def setImage(self , id , x , y ):
        d = f"setImage {id} {x} {y}"
        self.currentDisplay[(x,y)] = id
        self.send( d )
        
    def removeImage(self , x , y ):
        d = f"removeImage {x} {y}"
        if ( x, y ) in self.currentDisplay:
            self.currentDisplay.pop( (x,y) )
        self.send( d )
        
    def setXYImage(self , name, id, centerX , centerY , rotation , scale ):
        name = name.replace(" ","_") # if the name contains space, replace it by underscore
        d = f"setXYImage {name} {id} {centerX} {centerY} {rotation} {scale}"
        self.log( d )
        # todo: add local record of this to display it in the gui
        self.send( d )
        
    def removeXYImage(self , name ):
        d = f"removeXYImage {name}"
        self.log( d )
        # todo: add local record of this to display it in the gui
        self.send( d )
        
    def log(self, message ):
        logging.info(f"[TouchScreen][{self.comPort}][{self.name}]{message}")
        
    def send(self , message ):
        
        self.comManager.send( message )
        
        '''
        try:
            self.lock.acquire()
            self.log(f"Command:{message}")
            message=f"{message}\n"
            self.ser.write( message.encode("utf-8") )
            
        finally:
            self.lock.release()
        '''
        
    def fireEvent(self, deviceEvent ):        
        for listener in self.deviceListenerList:
            
            listener( deviceEvent )
    
    def addDeviceListener(self , listener ):
        self.deviceListenerList.append( listener )
        
    def removeDeviceListener(self , listener ):
        self.deviceListenerList.remove( listener )
        
    def showCalibration(self , show ):
        if show:
            self.send( "calibration show")
            self.displayCalibration = True
        else:
            self.send( "calibration hide")
            self.displayCalibration = False
        
    def __str__(self, *args, **kwargs):
        return "TouchScreen " + self.name+ " " + self.comPort
    
    def shutdown(self):
        self.enabled = False
        self.comManager.shutdown()
        
    def getCurrentImageList(self):
        return self.currentDisplay
    
if __name__ == '__main__':
    
    logging.basicConfig( level=logging.INFO ) 
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        
    def listener( event ):
        print( event )
        if "symbol touched" in event.description:
            x = event.data[1]
            y = event.data[2]
            ts.removeImage( x , y )
            ts.setImage( randint(0,2), randint(1,ts.nbCols), randint(1,ts.nbRows) )
            
        if "symbol xy touched" in event.description:
            name = event.data[0]
            print( f"symbol xy touched: name: {name}")
            ts.removeXYImage( name )
            ts.setXYImage( name , 12, randint(100,1820) , randint(100,980) , randint(0,360), random.random()/2+0.5 )
            #ts.setImage( randint(0,2), randint(1,ts.nbCols), randint(1,ts.nbRows) )
            
        print("Current display:")
        for pos,id in ts.getCurrentImageList().items():
            print ( f"{pos} : {id}"  )
        
    print("Starting touchScreen test.")
    ts = TouchScreen( comPort="COM60" )
    ts.addDeviceListener(listener)
    ts.setConfig( 3, 1, 350 )
    ts.clear()
    ts.setImage( randint(0,2), 1, 1 )
    ts.setImage( randint(0,2), 2, 1 )
    ts.setImage( randint(0,2), 3, 1 )
    #ts.setNormalMode()
    ts.setMouseMode()
    
    while True:
        print("coordinates: top left corner is 0,0")
        print("a: send ping")
        print("s: show random images")
        print("d/f: show/hide calibration and pointer on device")
        print("r: rat mode")
        print("m: mouse mode")
        print("n: normal mode (no touch translation/rotation, original screen)")
        print("g: grass hopper demo")
        print("y: add XY image")
        print("c: clear")
        print("z: force a crash on the device")        
        print("x: quit")
        print("t: thread call test")
        print("p: free placement of images")
        print("q: display all images")
        print("0: tests")
        print("1: 2 image test with framing")
        print("l 3 2 350 : show a layout of 3 cols per 2 rows with 350 image size")        
        a = input("command:")
        
        if a.startswith( "a" ):
            ts.ping()
        
        if "x" in a:
            ts.shutdown()
            quit()
        
        if "0" in a:
            ts.clear()
            ts.setXYImage( "left", 1, 1920/2-400,750,0,1 )
            ts.setXYImage( "bad", 6, 1920/2+400,750,0,1 )
            
        
        if "z" in a:
            ts.crash()            
        
        if "c" in a:
            ts.clear()            
            
        if "s" in a:
            ts.setImage( randint(0,16), randint(1,ts.nbCols), randint(1,ts.nbRows) )
            ts.setImage( randint(0,16), randint(1,ts.nbCols), randint(1,ts.nbRows) )
            ts.setImage( randint(0,16), randint(1,ts.nbCols), randint(1,ts.nbRows) )
        
        if "d" in a:
            ts.showCalibration( True )
            
        if "f" in a:
            ts.showCalibration( False )
            
        if "r" in a:
            ts.setRatMode()
        
        if "m" in a:
            ts.setMouseMode()
        
        if "n" in a:
            ts.setNormalMode()
            
        if "q" in a:
            for i in range(20):
                print( f"Showing image {i}")
                ts.setConfig( 2 , 1 , 300 )
                ts.setImage( i, 0, 1 )
                sleep(2)
            
        if "g" in a:
            GrassHopper( ts )
            
        if "p" in a:
            ts.clear()
            ts.setConfig( 1 , 1 , 500 )
            ts.setXYImage( "left", 1, 1920/2-400,750,0,1 )
            ts.setXYImage( "right", 4, 1920/2+400,750,0,1 )
            ts.showCalibration( False )

            margeout = 200
            g1 = GrassHopper( ts )
            #g1.scale = 0.5
            g1.setBounds( 1920/2-400-margeout, 750-margeout, 1920/2-400+margeout, 750+margeout)
            
            g2 = GrassHopper( ts )
            #g2.scale = 0.8
            g2.setBounds( 1920/2+400-margeout, 750-margeout, 1920/2+400+margeout, 750+margeout)
            
        if "t" in a:
            ThreadTest( ts )
            
        if "y" in a:
            ts.setXYImage( f"grasshopper{str(randint(0,1000))}" , 12, randint(100,1820) , randint(100,980) , randint(0,360), random.random()/2+0.5 )
        
        if a.startswith("1"):
            ts.setMouseMode()
            ts.setConfig( 1 , 1 , 800 )
            ts.clear()
            ts.setXYImage( "left", 1, 1920/2-400,750,0,1 )
            ts.setXYImage( "right", 1, 1920/2+400,750,0,1 )
        
        
        if a.startswith("l"):
            d = a.split( " " )
            ts.setConfig( int( d[1] ) , int( d[2] ), int ( d[3] ) )
            
            
            
    
    
    
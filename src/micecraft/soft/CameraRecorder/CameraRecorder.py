'''
Created on 21 juin 2024

@author: Fabrice de Chaumont

pip install opencv-python

'''
import datetime
import cv2 as cv
import threading
from random import randint
import logging

class XFrame(object):
    def __init__(self, frame, datetime ):
        self.frame = frame
        self.datetime = datetime
    
class CRText(object):
    
    def __init__(self, text, x, y , fontScale =1 , color=(240,240,240), bgColor=(50, 50, 50), centered = True, showBackGround = True, font = cv.FONT_HERSHEY_DUPLEX, centerX = False, minDateTime = None, maxDateTime = None ):
        self.text = text
        self.x = x
        self.y = y
        self.fontScale = fontScale
        self.color = color
        self.bgColor = bgColor
        self.centered = centered
        self.font = font
        self.showBackGround = showBackGround
        self.centerX = centerX
        self.minDateTime = minDateTime
        self.maxDateTime = maxDateTime
        
    def draw(self , frame, datetime=None ):
        
        show = True
        
        if datetime != None:
            if self.minDateTime != None:
                if datetime < self.minDateTime:
                    show=False
            if self.maxDateTime != None:
                if datetime > self.maxDateTime:
                    show=False
                    
        if show==False:
            return
        
        textSize = cv.getTextSize( self.text, self.font, fontScale=self.fontScale, thickness=1)[0]
        w = textSize[0]
        h = textSize[1]
        border = 10
        
        wf = frame.shape[1]
        hf = frame.shape[0]        
        
        xx = self.x
        yy = self.y
        
        if self.centered:
            xx = int ( self.x-w/2 )
            yy = int ( self.y-h/2 )
        
        if self.centerX:
            xx = int ( wf/2-w/2 )    
                
        if self.showBackGround:
            cv.rectangle( frame, ( xx-border, yy-border) , (xx+w+border,yy+h+border), self.bgColor ,-1 )
        cv.putText(frame, self.text, (xx, yy+h ), self.font, fontScale=self.fontScale, color=self.color )
        
        
class CameraRecorder(object):
    '''
    Multi-purpose recording object designed for webcam.
    
    Continuously streams a webcam. Only keeps the n last seconds in memory.
    User can then record post-event a video that was interesting.
    
    Can start/stop live record
    
    User can add overlay text while streaming or while saving
    
    '''
    
    def __init__(self, deviceNumber : int, bufferDurationS=5, showStream = True, name="SnapRecorder" , width=None, height = None, filePrefix = ""):
        
        self.name = name
        self.deviceNumber = deviceNumber
        
        self.showStream = showStream
        self.streamOut = None
        self.textList = []
        
        self.frameList = []
        self.bufferDurationS = bufferDurationS
        self.autoNumber = 1
        self.filePrefix = filePrefix
        
        self.windowName = None
        
        self.eventListListened = []
        
        print (f"{self.name} init...")
        self.cap = cv.VideoCapture( self.deviceNumber , cv.CAP_DSHOW)        
        #self.cap.set( cv.CAP_PROP_EXPOSURE, -1) 
        #print ( f"Camera exposure : {self.cap.get( cv.CAP_PROP_EXPOSURE)}" )
        
        if width != None:
            self.cap.set(cv.CAP_PROP_FRAME_WIDTH, width )
        if height != None:
            self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, height )
    
        print ( f"Camera resolution : {self.cap.get( cv.CAP_PROP_FRAME_WIDTH)} x {self.cap.get( cv.CAP_PROP_FRAME_HEIGHT)}" )
        print ( f"Camera exposure : {self.cap.get( cv.CAP_PROP_EXPOSURE)}" )
        print ( f"Camera brightness : {self.cap.get( cv.CAP_PROP_BRIGHTNESS)}" )
        print ( f"Camera gain : {self.cap.get( cv.CAP_PROP_GAIN)}" )
        print ( f"Camera auto exposure : {self.cap.get( cv.CAP_PROP_AUTO_EXPOSURE )}" )
        
        '''
        self.cap.set( cv.CAP_PROP_AUTO_EXPOSURE, 1 )
        self.cap.set( cv.CAP_PROP_EXPOSURE, 0.25 )
        '''
        
        # cv.CAP_PROP_BRIGHTNESS
        #self.cap.set( cv.CAP_PROP_BRIGHTNESS, 20 ) 
        
        print (f"{self.name} video capture setup ok.")
        
        self.enabled = True
        self.saveStreaming= False
        
        self.streamThread = threading.Thread(target=self.streamLoop , name = f"SnapRecorder streamloop - {self.name}")        
        self.streamThread.start()
        
    def bindDeviceToListen(self , device ):
        print( f"CameraRecorder #{self.deviceNumber}: Connect to device {device}")        
        device.addDeviceListener( self.listener )
    
    def unBindDeviceToListen(self , device ):
        device.removeDeviceListener( self.listener )
        
    def listener(self , event ):
        self.eventListListened.append( event )
    
    def clearOutDatedData(self):
        
        now = datetime.datetime.now()
        
        # clear old frames
        
        continueCheck = True
                
        while continueCheck:
            if len( self.frameList ) == 0:
                continueCheck=False
                
            if len ( self.frameList ) > 0:            
                if (now - self.frameList[0].datetime).total_seconds() > self.bufferDurationS:
                    self.frameList.pop( 0 )
                    continueCheck=True
                else:
                    continueCheck=False
                    
        # clear old events:
        continueCheck = True
        
        while continueCheck:
            if len ( self.eventListListened ) == 0:
                continueCheck=False
                
            if len ( self.eventListListened ) > 0:            
                if (now - self.eventListListened[0].datetime).total_seconds() > self.bufferDurationS:
                    self.eventListListened.pop( 0 )
                    continueCheck=True
                else:
                    continueCheck=False
                    
                
    def streamLoop(self):
        
        #out = cv.VideoWriter('output.mp4',fourcc, 30.0,(int(self.cap.get(3)),int(self.cap.get(4))))
                
        print( "start streaming...")
        
        while self.cap.isOpened() and self.enabled:
            
            ret, frame = self.cap.read()
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break

            now = datetime.datetime.now()
            date_time = now.strftime( "%d-%m-%Y %H:%M:%S.%f" )[:-4]

            w = frame.shape[1]
            h = frame.shape[0]
            
            
            self.centerText( date_time , w/2,h-40 , frame )
            
            
            for text in self.textList:
                text.draw( frame )
            
                                                                    
            self.frameList.append( XFrame( frame, now ) )
            
            
            self.clearOutDatedData()
            
                
            #print( len( self.frameList ) )
            
            self._saveStreaming( frame )
            
            
            if self.showStream:
                self.windowName = f'CamRecorder #{self.deviceNumber}'
                cv.imshow( self.windowName, frame)
            
            #self.cap.set( cv.CAP_PROP_BRIGHTNESS, 20 )

            cv.waitKey(1)
            '''
            if cv.waitKey(1) == ord('q'):
                break
            '''
            
        logging.info("Camera recorder: releasing...")
        # Release
        self.cap.release()
        #cv.destroyAllWindows()
        if self.windowName!=None:
            cv.destroyWindow( self.windowName )
        logging.info("Camera recorder: shutdown finished.")
        
    def _saveStreaming( self, frame ):
        
        if self.saveStreaming == True:
            
            if self.saveStreamingOutput == None:
                d = datetime.datetime.now().strftime( "%d-%m-%Y %Hh%Mm%S" )
                self.saveStreamingOutput = f"{self.filePrefix}{self.autoNumber:08d} - stream - {d}.mp4"
                self.autoNumber+=1
                
            if self.streamOut == None:
                fourcc = cv.VideoWriter_fourcc(*'FMP4')
                self.streamOut = cv.VideoWriter( self.saveStreamingOutput,fourcc, 30.0,(int(self.cap.get(3)),int(self.cap.get(4))))
        
            self.streamOut.write( frame )
        
        if self.saveStreaming == False:
            if self.streamOut!=None:                            
                self.streamOut.release()
                self.streamOut = None
    
    def saveStream(self, output = None ):
        self.saveStreamingOutput = output
        self.saveStreaming = True        
    
    def stopStream(self):
        self.saveStreaming = False

    def save(self , output=None, minDateTime=None, maxDateTime=None, textList = [] ):
        
        logging.info(f"[Camera Recorder] save output:{output} minDateTime:{minDateTime} maxDateTime:{maxDateTime}")
        print( f"output: {output}" )
        
        if output == None:
            d = datetime.datetime.now().strftime( "%d-%m-%Y %Hh%Mm%S" )
            output = f"{self.filePrefix}{self.autoNumber:08d} - {d}.mp4"
            self.autoNumber+=1            
        print( output )
        
        #fourcc = cv.VideoWriter_fourcc(*'FMP4')
        fourcc = cv.VideoWriter_fourcc('m', 'p', '4', 'v')
        #fourcc = cv.VideoWriter_fourcc('H', '2', '6', '4')
        
        
        out = cv.VideoWriter( output,fourcc, 30.0,(int(self.cap.get(3)),int(self.cap.get(4))))
        
        # draw events 
        
        for f in self.frameList:
            y = 20
            for event in self.eventListListened:
                            
                minDateTime = event.datetime
                maxDateTime = event.datetime + datetime.timedelta(seconds=3)
                
                if f.datetime>minDateTime and f.datetime<maxDateTime:
                    
                    text = CRText( event.description, 10, y, 0.5 )
                    y+=10
                    text.draw( f.frame )
                                    
        # draw text on frames
                
        for f in self.frameList:                        
            ok = True
            if minDateTime != None:
                if f.datetime<minDateTime:
                    ok = False
            
            if maxDateTime != None:
                if f.datetime>maxDateTime:
                    ok = False
            
            if ok:   
                for text in textList:
                    text.draw( f.frame,datetime = f.datetime )
                out.write(f.frame)
                        
        out.release()
    
    def delayedSave(self , delayS, output=None, minDateTime=None, maxDateTime=None, textList = [] ):
        # this will delay the save operation so that you can easily get a few seconds after the event to see what is happening after it.
        logging.info(f"[Camera Recorder] delayed save delayS:{delayS} output:{output} minDateTime:{minDateTime} maxDateTime:{maxDateTime}")
        t = threading.Timer( delayS, self.save, [output, minDateTime, maxDateTime, textList])
        t.start()
    
    def saveLastSeconds(self , nbSeconds, output=None, textList = [] ):
        self.save(output, datetime.datetime.now() - datetime.timedelta(seconds=nbSeconds) , textList = textList )
        
    def saveAll(self , output="all.mp4" ):        
        self.save(output)
    
    def shutdown(self):
        self.enabled = False
    
    
    def centerText( self, text, x,y , frame ):
        
        font = cv.FONT_HERSHEY_DUPLEX
        textSize = cv.getTextSize(text, font, fontScale=1, thickness=1)[0]
        w = textSize[0]
        h = textSize[1]
        border = 10
        
        xx = int ( x-w/2 )
        yy = int ( y-h/2 )    
        cv.rectangle( frame, ( xx-border, yy-border) , (xx+w+border,yy+h+border), (50, 50, 50) ,-1 )
        cv.putText(frame, text, (xx, yy+h ), font, fontScale=1.0, color=(240,240,240))
    
    def text( self, text, x,y , frame ):
        
        font = cv.FONT_HERSHEY_DUPLEX
        textSize = cv.getTextSize(text, font, fontScale=1, thickness=1)[0]
        w = textSize[0]
        h = textSize[1]
        border = 10
        xx = x
        yy = y
        cv.rectangle( frame, ( xx-border, yy-border) , (xx+w+border,yy+h+border), (50, 50, 50) ,-1 )
        cv.putText(frame, text, (xx, yy+h ), font, fontScale=1.0, color=(240,240,240))
    
    
    def clearText(self):
        self.textList.clear()
        
    def addText(self , crText ):
        self.textList.append( crText )
    
        
    


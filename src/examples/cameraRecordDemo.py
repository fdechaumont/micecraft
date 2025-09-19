'''
Created on 16 sept. 2025

@author: Fabrice de Chaumont

'''
from micecraft.soft.CameraRecorder.CameraRecorder import CameraRecorder, CRText
from random import randint
import datetime

if __name__ == '__main__':
    
    print("Sample Test CameraRecorder.")
        
    camRecorder = CameraRecorder( deviceNumber = 0, bufferDurationS=20, showStream = True )
        
    
    while True:
        
        print("5: save last 5 seconds")
        print("a: save all buffer")
        print("s: start saving stream")
        print("d: stop saving stream")        
        print("t: add random text")
        print("y: clear text")
        print("+: save from 5s before to 5s after call")
        print("w: add a text that will appear in a given time interval only")
        print("x: quit")
        
        command = input("command:")
        
        if "s" in command:
            camRecorder.saveStream( )
            
        if "d" in command:
            camRecorder.stopStream( )
        
        if "x" in command:
            camRecorder.shutdown()
            break
        
        if "a" in command:
            camRecorder.saveAll( output="all.mp4" )
            
        if "5" in command:
            txt = CRText( "last 5 seconds record" , 10 , 10 , centered=False , color=(0,0,255), showBackGround = False )
            camRecorder.saveLastSeconds( 5 , textList = [txt] )
            
        if "+" in command:
            text = CRText( "recorded 5 seconds before call to 5 seconds after call", 10, 10, fontScale=0.5,centerX = True )
            camRecorder.delayedSave( 5, minDateTime= datetime.datetime.now() - datetime.timedelta(seconds=5), textList =[text] )
            
        if "t" in command:            
            camRecorder.addText( CRText( "my text", randint(0,640),randint(0,480), centered=True, color = (randint(0,255),randint(0,255),randint(0,255)) , bgColor= (randint(0,255),randint(0,255),randint(0,255) ) ) ) 
            
        if "w" in command:
            text = CRText( "this will appear 1s before call, up to 1s after call" , 10 , 10 , centered=False , color=(0,0,255), showBackGround = False, minDateTime= datetime.datetime.now() - datetime.timedelta(seconds=1) , maxDateTime = datetime.datetime.now() + datetime.timedelta(seconds=1) )
            camRecorder.delayedSave( 5, minDateTime= datetime.datetime.now() - datetime.timedelta(seconds=5), textList =[text] )
    
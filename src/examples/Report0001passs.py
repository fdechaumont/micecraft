'''
Created on 29 sept. 2025

@author: Fab
'''

import os
from datetime import datetime
from micecraft.soft.report.WebSite import WebSite
from micecraft.soft.report.Report import Report
import webbrowser

if __name__ == '__main__':
        
    print( f"Starting report generation example at {datetime.now()}")
    
    startComputationTime = datetime.now()

    # set output folder
    currentFolder = os.path.dirname(os.path.abspath(__file__))    
    outFolder = currentFolder+"/html_output/"
    
    # create the object WebSite    
    webSite = WebSite( outFolder=outFolder )
    
    # remove existing files in out folder
    webSite.initWebSiteOutFolder( )
    
    # create a report on the main page    
    webSite.addReport( Report( "Report title", f"Here is a <b>Description</b>." , experimentName="main" ) )

    # generate the WebSite based on the reports.
    webSite.generateWebSite( )
    
    # open the website in your browser.
    webbrowser.open( f"{outFolder}/index.html" )
        
    print("Done.")

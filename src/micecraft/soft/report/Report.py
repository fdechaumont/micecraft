'''
Created on 5 févr. 2025

@author: Fab
'''

import os

from jinja2 import Environment, FileSystemLoader

from datetime import datetime
from micecraft.soft.report.ReportTools import clean_filename


'''
# Create the jinja2 environment.
current_directory = os.path.dirname(os.path.abspath(__file__))
env = Environment(loader=FileSystemLoader(current_directory))
'''

class Report(object):

    def __init__(self , title, data, template="contentCard.html", experimentName="experiment",  style = "primary", options= {} ):
        
        self.title = title
        self.data = data
        self.template = template
        self.experimentName = experimentName
        self.style = style # can be: primary, success, danger, warning
        self.options = options
    
    def __str__(self, *args, **kwargs):
        return f"Report {self.title} - {self.experimentName}"
    
    def render(self , templateFolder, outFolder=None, reportList=None ):

        print(f"Rendering {self.experimentName} - {self.title} - {self.template}")
        env = Environment(loader=FileSystemLoader(templateFolder))
        
        numberInTitle = ""
        if reportList != None:
            number = reportList.index( self )
            numberInTitle = f"#{number} - "

        if self.template == "splitter.html":
            numberInTitle =""

        if self.template == "table.html":
            if outFolder == None:
                print("Error: This export needs outFolder")
                quit()
                
            df = self.data
            s = f"{self.experimentName} {self.title}"
            s = clean_filename( s )
            fileNameXLS = f"{s}.xlsx"
            df.to_excel( f"{outFolder}/{fileNameXLS}" )
            print(f"Xlsx file is : {fileNameXLS}")
            render = env.get_template( self.template ).render( title=numberInTitle+self.title, content=self.data, fileNameXLS=fileNameXLS, style=self.style, **self.options )
            
            
            return render
        
        
        render = env.get_template( self.template ).render( title=numberInTitle+self.title, content=self.data, style = self.style, **self.options )
        
        return render
        
        
        
        
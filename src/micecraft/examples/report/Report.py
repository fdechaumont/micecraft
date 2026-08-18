"""
Created on 5 févr. 2025

@author: Fab
"""

import os
import logging
from typing import Any

import pandas as pd
from jinja2 import Environment, FileSystemLoader

from micecraft.examples.report.ReportTools import clean_filename

"""
# Create the jinja2 environment.
current_directory = os.path.dirname(os.path.abspath(__file__))
env = Environment(loader=FileSystemLoader(current_directory))
"""


class Report(object):

    def __init__(
        self,
        title,
        data,
        template="contentCard.html",
        experimentName="main",
        style="primary",
        options={},
    ):

        self.title: str = title
        self.data: Any = data
        self.template: str = template
        self.experimentName: str = experimentName
        self.style: str = style  # can be: primary, success, danger, warning
        self._errorLevel: int = (
            0  # override the style if different from 0. 1: warning, 2:danger
        )
        self.options: dict = options
        self.downloadableContent: dict[str, Any] = (
            {}
        )  # to add dataframe or files that will be available for download. Key is the name of the link on the webpage.

    def __str__(self, *args, **kwargs):
        return f"Report {self.title} - {self.experimentName}"

    def setDownloadableContent(self, name, content):
        """
        content supports dataframe
        """
        self.downloadableContent[name] = content

    def setErrorLevel(self, errorLevel):
        self._errorLevel = errorLevel
        # overrides default style with errorLevel
        if self._errorLevel == 1:
            self.style = "success"
        if self._errorLevel == 1:
            self.style = "warning"
        if self._errorLevel == 2:
            self.style = "danger"

    def getErrorLevel(self):
        return self._errorLevel

    def render(self, templateFolder, outFolder=None, reportList=None):

        logging.debug(
            f"Rendering {self.experimentName} - {self.title} - {self.template}"
        )
        env = Environment(loader=FileSystemLoader(templateFolder))

        numberInTitle = ""
        if reportList != None:
            number = reportList.index(self)
            numberInTitle = f"#{number} - "

        if self.template == "splitter.html":
            numberInTitle = ""

        if self.template == "table.html":
            if outFolder == None:
                logging.error("This export needs outFolder")
                quit()

            df = self.data
            s = f"{self.experimentName} {self.title}"
            s = clean_filename(s)
            fileNameXLS = f"{s}.xlsx"
            df.to_excel(f"{outFolder}/{fileNameXLS}")
            logging.debug(f"Xlsx file is : {fileNameXLS}")
            render = env.get_template(self.template).render(
                title=numberInTitle + self.title,
                content=self.data,
                fileNameXLS=fileNameXLS,
                style=self.style,
                **self.options,
            )

            return render

        # add extra content
        extraDownloadContent = ""

        for k, v in self.downloadableContent.items():
            if isinstance(v, pd.DataFrame):
                df = v
                s = f"{self.experimentName} {self.title} {k}"
                s = clean_filename(s)
                fileNameXLS = f"{s}.xlsx"
                df.to_excel(f"{outFolder}/{fileNameXLS}")
                logging.debug(f"Xlsx file is : {fileNameXLS}")
                extraDownloadContent += f"<a href='{fileNameXLS}' >{k}</a><br>"
            else:
                logging.error(
                    f"Report rendering, downloadableContent: Can't process data of type {type(v)}"
                )
                logging.error(v)
                quit()

        render = env.get_template(self.template).render(
            title=numberInTitle + self.title,
            content=self.data,
            style=self.style,
            extraDownloadContent=extraDownloadContent,
            **self.options,
        )

        return render

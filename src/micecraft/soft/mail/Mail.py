'''
Created on 7 juin 2022

@author: Fabrice de Chaumont

'''

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from smtplib import SMTPSenderRefused
from threading import Thread
import logging
    

class Mail:

    # variables shared by all Mail instances. Use Mail.config() to set them all:
    port = None
    smtp_server_domain_name = None
    sender_mail = None
    password = None
    
    def __init__(self ):
        pass

    @staticmethod
    def config( port, smtp_server_domain_name, sender_mail, password ):
        Mail.port = port
        Mail.smtp_server_domain_name = smtp_server_domain_name
        Mail.sender_mail = sender_mail
        Mail.password = password

    def sendInfo(self , emails, subject, content, files = None):
        subject = "[LMT-AUTO][Info] "+ subject
        self.sendThreaded(emails, subject, content, files)                
    
    def sendAlert(self , emails, subject, content, files = None):
        subject = "[LMT-AUTO][Alert] "+ subject
        self.sendThreaded(emails, subject, content, files)
    
    def sendThreaded( self , emails, subject, content, files = None):
        thr = Thread(target=self.send, args=[emails, subject, content , files])
        thr.start()

    def send(self, emails, subject, content , files = None ):
                
        if len( emails ) == 0:
            logging.info("Mailing error: no email set.")
            return
            
        ssl_context = ssl.create_default_context()
        
        try:
            service = smtplib.SMTP_SSL(self.smtp_server_domain_name, self.port, context=ssl_context)
                        
        except Exception as e:
            logging.info("Mailing error (no internet ?):" + str( e ))
            return False
            
        service.login(self.sender_mail, self.password)
        
        #for email in emails:
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = self.sender_mail
        msg['To'] = ", ".join( emails )
        
        msg.attach(MIMEText(content))

        
        # attach files
        if files!=None:
            for file_path in files:
                
                mimeBase = MIMEBase("application", "octet-stream")
                with open(file_path, "rb") as file:
                    mimeBase.set_payload(file.read())
                encoders.encode_base64(mimeBase)
                mimeBase.add_header("Content-Disposition", f"attachment; filename={Path(file_path).name}")
                msg.attach(mimeBase)
        
        # send mail
        logging.info("Sending email " + str( subject ) )
        try:
            service.sendmail(self.sender_mail, emails, msg.as_string() )
        except SMTPSenderRefused as e :
            # file too big
            logging.info("Mailing error:"+str(e))
            
        except Exception as e:
            logging.info("Mailing error:" + str( e ))
            


        service.quit()
        return True


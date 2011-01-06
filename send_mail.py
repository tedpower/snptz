import logging
import datetime
from google.appengine.api import mail
from google.appengine.api import users

logging.info('Scheduled task ran.')

message_body = '''

Hi Ted,

-----------------------------------------
WHAT'RE YOU GOING TO DO THIS WEEK?
-----------------------------------------




-----------------------------------------
HOW DID LAST WEEK GO?
-----------------------------------------




-----------------------------------------

Your last snippet:
- 

'''

message = mail.EmailMessage(
  sender='SNPTZ <ted@snptz.com>',
  to='tedpower@gmail.com',
  reply_to='SNPTZ <mail@snptzapp.appspotmail.com>',
  subject='SNPTZ',
  body=message_body)

message.send()
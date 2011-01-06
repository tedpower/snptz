import logging
import datetime
from google.appengine.api import mail
from google.appengine.api import users
import models

logging.info('Scheduled task ran.')

message_body = '''

Hi USERRRRR,

-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
HOW DID LAST WEEK GO?
Edit your stated goals from last week:
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

- A
- B
- D

--~~--~~--~~--~~--~~--~~--~~--~~--~~--~
WHAT'RE YOU GOING TO DO THIS WEEK?
~~--~~--~~--~~--~~--~~--~~--~~--~~--~--



'''

que = db.Query(models.User)
user_list = que.fetch(limit=100)

for user in user_list:

  message = mail.EmailMessage(
    sender='SNPTZ <ted@snptz.com>',
    to=user.googUser,
    reply_to='SNPTZ <mail@snptzapp.appspotmail.com>',
    subject='SNPTZ',
    body=message_body)

  message.send()
#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import logging
import datetime
from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import db
import models

logging.info('Scheduled task ran.')

plaintext_template = '''

Hi %(username),

-----------------------------------------
HOW DID LAST WEEK GO?
Edit your goals from last week:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

%(tasks)
-----------------------------------------
WHAT'RE YOU GOING TO DO THIS WEEK?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


'''

html_template = '''

<img src="http://www.snptz.com/static/logoEmail.png" width="174" height="50" alt="SNPTZ">
<p>Hi %(username)!</p>

'''

que = db.Query(models.User)
user_list = que.fetch(limit=100)

for user in user_list:
    # get the list of what the user planned to do last time
    last_tasks = user.last_past_taskweek.optimistic
    # join all the tasks with linebreaks
    tasks_as_lines = "\n".join(last_tasks)
    # personalize the message_template
    personalized_plaintext_message = plaintext_template % {"username": user.first_name, "tasks": tasks_as_lines}
    personalized_html_message = html_template % {"username": user.first_name, "tasks": tasks_as_lines}

    message = mail.EmailMessage(
      sender='SNPTZ <ted@snptz.com>',
      to=user.email,
      reply_to='SNPTZ <mail@snptzapp.appspotmail.com>',
      subject='SNPTZ',
      body=personalized_plaintext_message,
      htmo=personalized_html_message)

    message.send()

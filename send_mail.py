#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import logging
import datetime
from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import db
import models

logging.info('Scheduled task ran.')

message_template = '''

Hi %(username),

~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
HOW DID LAST WEEK GO?
Edit your stated goals from last week:
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

%(tasks)
--~~--~~--~~--~~--~~--~~--~~--~~--~~--~
WHAT'RE YOU GOING TO DO THIS WEEK?
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-


'''

que = db.Query(models.User)
user_list = que.fetch(limit=100)

for user in user_list:
    # get the list of what the user planned to do last time
    last_tasks = user.last_past_taskweek.optimistic
    # join all the tasks with linebreaks
    tasks_as_lines = "\n".join(last_tasks)
    # personalize the message_template
    personalized_message = message_template % {"username": user.first_name, "tasks": tasks_as_lines}

    message = mail.EmailMessage(
      sender='SNPTZ <ted@snptz.com>',
      to=user.email,
      reply_to='SNPTZ <mail@snptzapp.appspotmail.com>',
      subject='SNPTZ',
      body=personalized_message)

    message.send()

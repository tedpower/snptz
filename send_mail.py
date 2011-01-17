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

Hi %(username)s,

-----------------------------------------
HOW DID LAST WEEK GO?
Edit your goals from last week:
-----------------------------------------

%(tasks)s
-----------------------------------------
WHAT'RE YOU GOING TO DO THIS WEEK?
-----------------------------------------


'''

html_template = '''

<img src="http://www.snptz.com/static/logoMed.png" width="174" height="50" alt="SNPTZ">
<p>Good morning %(username)s!</p>

<pre>
-----------------------------------------
HOW DID LAST WEEK GO?
Edit your goals from last week:
-----------------------------------------
</pre>

%(tasks)s
<pre>
-----------------------------------------
WHAT'RE YOU GOING TO DO THIS WEEK?
-----------------------------------------
</pre>
'''

first_time_plaintext = '''

Hi %(username)s,

Welcome to SNPTZ!
Tell us a few things you are going to be working on this week in the space below.
Don't get too detailed or wordy. Each week, we'll follow up so you can reflect on your progress.

-----------------------------------------
WHAT'RE YOU GOING TO DO THIS WEEK?
-----------------------------------------


'''

first_time_html = '''

<img src="http://www.snptz.com/static/logoMed.png" width="174" height="50" alt="SNPTZ">
<p>Good morning %(username)s!</p>
Welcome to SNPTZ!
Tell us a few things you are going to be working on this week in the space below.
Don't get too detailed or wordy. Each week, we'll follow up so you can reflect on your progress.
<pre>
-----------------------------------------
WHAT'RE YOU GOING TO DO THIS WEEK?
-----------------------------------------
</pre>
'''

# q = db.GqlQuery("SELECT * FROM models.Profile " +
#                 "WHERE weekly_email = :1",
#                 "True")
# user_list = q.fetch(5)

q = models.Profile.all()
q.filter('weekly_email = ', True)
user_list = q.fetch(100)
logging.info("there are %s users" %(len(user_list)))

for user in user_list:
    logging.info("user is %s" % (user.first_name))
    # get the list of what the user planned to do last time
    last_past = user.freshest_taskweek
    if user.first_name is not None:
        first_name = user.first_name
    if last_past is not None:
        # join all the tasks with linebreaks
        tasks_as_lines = user.freshest_taskweek.optimistic_as_str
        # personalize the message_template
        personalized_plaintext_message = plaintext_template % {"username": first_name, "tasks": tasks_as_lines}
        personalized_html_message = html_template % {"username": first_name, "tasks": tasks_as_lines}
    else:
        personalized_html_message = first_time_html % {"username": first_name}
        personalized_plaintext_message = first_time_plaintext % {"username": first_name}

    message = mail.EmailMessage(
      sender='SNPTZ <weekly@snptz.com>',
      to=user.email,
      reply_to='SNPTZ <mail@snptzapp.appspotmail.com>',
      # TODO make the subject of the email include the date
      subject='SNPTZ for %s' % datetime.datetime.now().strftime("%b %d"),
      body=personalized_plaintext_message,
      html=personalized_html_message)

    message.send()

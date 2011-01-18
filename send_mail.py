#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import logging
import datetime
from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import db
import models

logging.info('Scheduled task starting...')

plaintext_template = '''

Hi %(username)s,

Please reply to this email and describe
(inline, below) what you worked on last
week and what you are going to work on
this week (one task per line, please).

Be sure to send your reply before lunch...
otherwise we'll tell your colleagues that
you are planning to slack off all week :)

--~--~--~--~--~--~--~--~--~--~--~--~--~--~
HOW DID LAST WEEK GO?
Edit your goals from last week:
--~--~--~--~--~--~--~--~--~--~--~--~--~--~

%(tasks)s
--~--~--~--~--~--~--~--~--~--~--~--~--~--~
WHAT'RE YOU GOING TO DO THIS WEEK?
--~--~--~--~--~--~--~--~--~--~--~--~--~--~




--
(list any number of tasks above these two hyphens)
'''

html_template = '''

<img src="http://www.snptz.com/static/logoMed.png" width="174" height="50" alt="SNPTZ">
<p>Good morning %(username)s!</p>

<p>
Please reply to this email and describe
(inline, below) what you worked on last
week and what you are going to work on
this week (one task per line, please).

Be sure to send your reply before lunch...
otherwise we'll tell your colleagues that
you are planning to slack off all week :)
</p>
<pre>
--~--~--~--~--~--~--~--~--~--~--~--~--~--~
HOW DID LAST WEEK GO?
Edit your goals from last week:
--~--~--~--~--~--~--~--~--~--~--~--~--~--~
</pre>

%(tasks)s
<pre>
--~--~--~--~--~--~--~--~--~--~--~--~--~--~
WHAT'RE YOU GOING TO DO THIS WEEK?
--~--~--~--~--~--~--~--~--~--~--~--~--~--~
</pre>




<pre>
--
(list any number of tasks above these two hyphens)
</pre>
'''

first_time_plaintext = '''

Hi %(username)s,

Welcome to SNPTZ!

Please hit reply and tell us a few things you are going
to work on this week in the space below (reply inline).
Don't get too detailed or wordy -- SNPTZ isn't a to-do list or an issue tracker.
Also, don't get creative with formatting your reply (our email parsing code is really basic).
Each week, we'll follow up so you can reflect on your progress --
and share your plans with your esteemed colleagues (if they use SNPTZ too).

--~--~--~--~--~--~--~--~--~--~--~--~--~--~
WHAT'RE YOU GOING TO DO THIS WEEK?
--~--~--~--~--~--~--~--~--~--~--~--~--~--~




--
(list any number of tasks above these two hyphens)
'''

first_time_html = '''

<img src="http://www.snptz.com/static/logoMed.png" width="174" height="50" alt="SNPTZ">
<p>Good morning %(username)s!</p>
Welcome to SNPTZ!
<p>
Please hit reply and tell us a few things you are going
to work on this week in the space below (reply inline).
Don't get too detailed or wordy -- SNPTZ isn't a to-do list or an issue tracker.
Also, don't get creative with formatting your reply (our email parsing code is really basic).
Each week, we'll follow up so you can reflect on your progress --
and share your plans with your esteemed colleagues (if they use SNPTZ too).
</p>
<pre>
--~--~--~--~--~--~--~--~--~--~--~--~--~--~
WHAT'RE YOU GOING TO DO THIS WEEK?
--~--~--~--~--~--~--~--~--~--~--~--~--~--~
</pre>




<pre>
--
(list any number of tasks above these two hyphens)
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

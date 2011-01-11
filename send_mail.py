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

<img src="http://www.snptz.com/static/logoEmail.png" width="174" height="50" alt="SNPTZ">
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

<img src="http://www.snptz.com/static/logoEmail.png" width="174" height="50" alt="SNPTZ">
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

que = db.Query(models.Profile)
que = que.filter('weekly_email= ', 'True')
user_list = que.fetch(limit=100)

for user in user_list:
    # get the list of what the user planned to do last time
    last_past = user.last_past_taskweek
    last_tasks = []
    if user.first_name is not None:
        first_name = user.first_name
    if last_past is not None:
        last_tasks = user.last_past_taskweek.optimistic
        # join all the tasks with linebreaks
        tasks_as_lines = "\n".join(last_tasks)
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

    def construct_digest(profile_list):
        personalized_digest_plaintext = '''
            Hi %(username)s,

            Here's what your esteemed colleagues are up to this week:


        '''

        for profile in profile_list:
            template = '''
            %(colleague_nick)s (%s(colleague_teams)s)
            ---------------------
            %(colleague_tasks)s

            '''
            prof_name = profile.nickname
            prof_team_names = ", ".join([m.team.name for m in profile.membership_set])
            prof_taskweek = profile.this_weeks_taskweek
            if len(prof_tasks) == 0:
                prof_tasks = "just chillin... (no reported tasks!)"
            else:
                prof_tasks = "\n".join(prof_taskweek)

            personalized_digest_plaintext = personalized_digest_plaintext +\
                template % {"colleague_nick": prof_name,
                            "colleague_teams": prof_team_names,
                            "colleague_tasks": prof_tasks}
        return personalized_digest_plaintext

    esteemed_colleages = user.esteemed_colleagues
    if esteemed_colleagues is not None:
        digest_message_body = construct_digest(esteemed_colleagues) % {"username": first_name}

        digest = mail.EmailMessage(
        sender='SNPTZ Esteemed Colleagues <digest@snptz.com>',
        to=user.email,
        reply_to='SNPTZ <mail@snptzapp.appspotmail.com>',
        # TODO make the subject of the email include the date
        subject='SNPTZ Esteemed Colleagues digest for %s' % datetime.datetime.now().strftime("%b %d"),
        body=personalized_digest_plaintext)

        digest.send()

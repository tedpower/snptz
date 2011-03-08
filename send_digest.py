#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import logging
import time
import datetime
import random
from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import db
import models

logging.info('Scheduled task starting...')

def construct_digest(nickname, profile_list):
    digest_greeting = '''
Hi %(username)s,

Here's what your esteemed colleagues are up to this week:


    '''
    # format digest_greeting with user's first_name
    personalized_digest_plaintext = digest_greeting % {"username": nickname}

    for profile in profile_list:
        colleague_summary = '''
%(colleague_nick)s (%(colleague_teams)s)
---------------------
%(colleague_tasks)s

        '''
        # find something to use to identify this colleague
        prof_name = profile.first_name
        if prof_name is None:
            prof_name = profile.nickname

        # list all team names this colleague belongs to
        prof_team_names = ", ".join([m.team.name for m in profile.membership_set])
        prof_taskweek = profile.this_weeks_tw
        # TODO refactor control flow. this is whack
        if prof_taskweek is not None:
            prof_taskweek = prof_taskweek.optimistic
        if prof_taskweek is None:
            fake_tasks = [
                "putting feet up all week",
                "sleeping on the job each day",
                "taking really really long lunch breaks",
                "productivity consumed by facebook bender",
                "researching 1000 best cute animal videos",
                "catching up on reality TV",
                "just chillin",
                "secretly daytrading all day",
                "'working from home' at the beach"]
            prof_tasks = random.choice(fake_tasks) + "\n(no reported tasks this week!)"
        else:
            prof_tasks = "\n".join(prof_taskweek)

        personalized_digest_plaintext = personalized_digest_plaintext +\
             colleague_summary % {"colleague_nick": prof_name,
                        "colleague_teams": prof_team_names,
                        "colleague_tasks": prof_tasks}
    return personalized_digest_plaintext

user_list = models.Profile.all()

for user in user_list:
    if not user.weekly_email:
        continue

    # get a list of this user's esteemed_colleagues
    esteemed_colleagues = user.esteemed_colleagues
    if esteemed_colleagues is not None:
        # get user's first_name
        # (or use nickname if first_name isnt specified)
        nick = user.first_name
        if nick is None:
            nick = user.nickname

        # construct a personalized message body
        digest_message_body = construct_digest(nick, esteemed_colleagues)

        digest = mail.EmailMessage(
        sender='SNPTZ <weekly@snptz.com>',
        to=user.email,
        reply_to='SNPTZ <mail@snptzapp.appspotmail.com>',
        # TODO make the subject of the email include the date
        subject='SNPTZ Esteemed Colleagues digest for %s' % datetime.datetime.now().strftime("%b %d"),
        body=digest_message_body)

        digest.send()
        # as far as i can tell from http://code.google.com/appengine/docs/quotas.html#Mail
        # up to 8 email recipients per minute is free.
        # 60 seconds / 8 recipients = 7.5 seconds between each
        # so, sleep for 8 seconds after sending
        # before continuing in the for loop
        # TODO maybe using task queue is better?
        time.sleep(8)

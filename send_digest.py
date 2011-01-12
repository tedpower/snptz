#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import logging
import datetime
from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import db
import models

logging.info('Scheduled task ran.')

def construct_digest(nickname, profile_list):
    digest_template = '''
        Hi jackass,

        Here's what your esteemed colleagues are up to this week:


    '''
    personalized_digest_plaintext = digest_template# % {"username": nickname}

    for profile in profile_list:
        template = '''
        %(colleague_nick)s (%s(colleague_teams)s)
        ---------------------
        %(colleague_tasks)s

        '''
        prof_name = profile.nickname
        prof_team_names = ", ".join([m.team.name for m in profile.membership_set])
        prof_taskweek = profile.this_weeks_taskweek
        # TODO refactor control flow. this is whack
        if prof_taskweek is not None:
            prof_taskweek = prof_taskweek.optimistic
        if prof_taskweek is None:
            prof_tasks = "just chillin... (no reported tasks!)"
        else:
            prof_tasks = "\n".join(prof_taskweek)

        personalized_digest_plaintext = personalized_digest_plaintext +\
            template % {"colleague_nick": prof_name,
                        "colleague_teams": prof_team_names,
                        "colleague_tasks": prof_tasks}
    return personalized_digest_plaintext

user_list = []
user_list.append(models.Profile.find_by_email('evanmwheeler@gmail.com'))
user_list.append(models.Profile.find_by_email('tedpower@gmail.com'))

for user in user_list:

    esteemed_colleagues = user.esteemed_colleagues
    if esteemed_colleagues is not None:
        digest_message_body = construct_digest(user.first_name, esteemed_colleagues)

        digest = mail.EmailMessage(
        sender='SNPTZ Esteemed Colleagues <digest@snptz.com>',
        to=user.email,
        reply_to='SNPTZ <mail@snptzapp.appspotmail.com>',
        # TODO make the subject of the email include the date
        subject='SNPTZ Esteemed Colleagues digest for %s' % datetime.datetime.now().strftime("%b %d"),
        body=digest_message_body)

        digest.send()

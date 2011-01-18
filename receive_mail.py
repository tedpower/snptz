#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp import mail_handlers
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from google.appengine.ext import db
import models
import re
from datetime import datetime, timedelta

class MyMailHandler(mail_handlers.InboundMailHandler):
    def receive(self, message):
        
        # # Check to see if the message is plaintext or HTML        
        # content_type = message.original.get_content_type()
        # logging.info("the content type is %s" % content_type)
        # 
        # if content_type == 'text/html' or content_type == 'multipart/alternative':
        #     html_bodies = message.bodies('text/html')
        #     for content_type, body in html_bodies:
        #         decoded_message = stripHTML(body.decode())
        # elif content_type == 'text/plain':
        #     plaintext_bodies = message.bodies('text/plain')
        #     for content_type, body in plaintext_bodies:
        #         decoded_message = body.decode()

        plaintext_bodies = message.bodies('text/plain')
        for content_type, body in plaintext_bodies:
            decoded_message = body.decode()

        logging.info('Received email message from %s: %s' % (message.sender,
                                                                 decoded_message))
        
        # clean up the email address
        pattern = re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}')
        cleanedEmail = pattern.findall(message.sender)
        from_email = cleanedEmail[0]
        logging.info('the user is %s' % (cleanedEmail[0]))

        # find the good bits of the email

        # this regex matches one or more repetitions of '--~'
        breaking_pattern = re.compile(r'(\-\-\~)+', re.MULTILINE)
        # this regex matches two hyphens
        end_pattern = re.compile(r'(\-\-)', re.MULTILINE)

        # split email on breaking_pattern
        split_email = re.split(breaking_pattern, decoded_message)

        # see if this is a reply to the first-time welcome message
        # TODO is there a more reliable way of doing this?
        welcome_message = decoded_message.find("Welcome to SNPTZ!")

        # handy variable to keep track of whether or not we are
        # dealing with a reply to the first-time welcome message or not
        first_time = False if welcome_message == -1 else True

        if not first_time:
            # split_email[0] is everything up to Good Morning user!
            # split_email[1] is --~
            # split_email[2] is the HOW DID LAST WEEK GO... text
            # split_email[3] is --~
            last_week_raw = split_email[4]
            last_week_split = last_week_raw.splitlines()
            lastWeek = cleanLines(last_week_split)

            logging.info("last week: %s" % lastWeek)

            # split_email[5] is --~
            # split_email[6] is WHAT'RE YOU GOING ... text
            # split_email[7] is --~

            # split_email[8] is this weeks tasks, along with everything else (signature, etc)
            # so split it on the end_pattern and the first item should be this weeks tasks
            this_week_raw = re.split(end_pattern, split_email[8])[0]
            this_week_split = this_week_raw.splitlines()
            thisWeek = cleanLines(this_week_split)
        else:
            # split_email[0] is intro paragraph
            # split_email[1] is --~
            # split_email[2] is WHAT'RE YOU GOING ... text
            # split_email[3] is --~
            this_week_raw = re.split(end_pattern, split_email[4])[0]
            this_week_split = this_week_raw.splitlines()
            thisWeek = cleanLines(this_week_split)

        logging.info("this week: %s" % thisWeek)

        # create a Message object to store the email, etc
        # don't put yet because we may add a user reference
        newmessage = models.Message(sender=cleanedEmail[0], body=decoded_message)

        # find the user
        user = models.Profile.find_by_email(from_email)
        logging.info("user is %s" % user)
        if user is not None:
            newmessage.userRef = user

            if not first_time:
                # deal with freshest_taskweek before creating a new one!
                # (otherwise user.freshest_taskweek will return the newly
                # created taskweek created by user.this_weeks_tw)
                last_taskweek = user.freshest_taskweek
                if last_taskweek is not None:
                    last_taskweek.realistic = lastWeek
                    last_taskweek.put()
                # TODO do something if there are no past taskweeks?

            # get or create a new taskweek for this week
            # ... meaning we will overwrite the tasks if this is the
            # second email from this user this week
            new_taskweek = user.this_weeks_tw
            new_taskweek.optimistic = thisWeek
            new_taskweek.put()
        else:
            # TODO user is not known -- tell them to sign up
            logging.info("OOPS. UNKNOWN USER: %s" % from_email)

        # save the incoming message, which has had a user reference
        # added (if the user is known)
        newmessage.put()

def cleanLines(weekList):
    tempList = []
    for i in weekList:
        # remove quote mark
        i = i.replace('>', '')
        # remove any leading/trailing whitespace
        i = i.strip()
        if (len(i) != 0):
            tempList.append(i)
    return tempList


application = webapp.WSGIApplication([MyMailHandler.mapping()],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

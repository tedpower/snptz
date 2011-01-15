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

from stripper import stripHTML

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
        breaking_string = "-----------------------------------------"
        start = decoded_message.find(breaking_string)
        start = decoded_message.find(breaking_string, start + 1)
        end = decoded_message.find(breaking_string, start + 1)
        lastWeek = decoded_message[start + len(breaking_string):end]
        lastWeek = lastWeek.splitlines()
        lastWeek = cleanLines(lastWeek)
        logging.info("last week: %s" % lastWeek)
        start = decoded_message.find(breaking_string, end + 1)
        thisWeek = decoded_message[start + len(breaking_string):]
        thisWeek = thisWeek.splitlines()
        thisWeek = cleanLines(thisWeek)
        logging.info("this week: %s" % thisWeek)

        # create a Message object to store the email, etc
        # don't put yet because we may add a user reference
        newmessage = models.Message(sender=cleanedEmail[0], body=decoded_message)

        # find the user
        user = models.Profile.find_by_email(from_email)
        logging.info("user is %s" % user)
        if user is not None:
            newmessage.userRef = user

            # deal with last_past_taskweek before creating a new one!
            # (otherwise user.last_past_taskweek will return the newly
            # created taskweek created by user.this_weeks_taskweek)
            last_taskweek = user.last_past_taskweek
            if last_taskweek is not None:
                last_taskweek.realistic = lastWeek
                last_taskweek.put()
            # TODO do something if there are no past taskweeks?

            # get or create a new taskweek for this week
            # ... meaning we will overwrite the tasks if this is the
            # second email from this user this week
            new_taskweek = user.this_weeks_taskweek
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

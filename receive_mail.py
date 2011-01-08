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

class MyMailHandler(mail_handlers.InboundMailHandler):
    def receive(self, message):
        html_bodies = message.bodies('text/html')
        for content_type, body in html_bodies:
            decoded_html = body.decode()

        logging.info('Received email message from %s: %s' % (message.sender,
                                                                 decoded_html))

        # clean up the email address
        pattern = re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}')
        cleanedEmail = pattern.findall(message.sender)
        from_email = cleanedEmail[0]
        logging.info('the user is %s' % (cleanedEmail[0]))

        # find the good bits of the email
        breaking_string = "~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-"
        start = decoded_html.find(breakingString)
        start = decoded_html.find(breakingString, start + 1)
        end = decoded_html.find(breakingString, start + 1)
        thisWeek = decoded_html[start + len(breakingString):end]
        thisWeek = thisWeek.splitlines()
        thisWeek = cleanLines(thisWeek)
        start = decoded_html.find(breakingString, end + 1)
        end = decoded_html.find(breakingString, start + 1)
        lastWeek = decoded_html[start + len(breakingString):end]
        lastWeek = lastWeek.splitlines()
        lastWeek = cleanLines(lastWeek)

        # create a Message object to store the email, etc
        # don't put yet because we may add a user reference
        newmessage = models.Message(sender=cleanedEmail[0], body=decoded_html)

        # find the user
        user = models.Profile.find_by_email(from_email)
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
            pass

        # save the incoming message, which has had a user reference
        # added (if the user is known)
        newmessage.put()

def cleanLines(weekList):
    tempList = []
    for i in weekList:
        if (len(i) != 0) and (i.isspace() == False):
            tempList.append(i)
    return tempList


application = webapp.WSGIApplication([MyMailHandler.mapping()],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

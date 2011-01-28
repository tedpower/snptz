#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os
import logging
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
import models

class Signup(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        
        profile = models.Profile.get_by_key_name(user.user_id())
        if profile is None:
            doRender(self, 'signup.html', {'user_email' : user.email()})
        else:
            self.redirect('/');

    def post(self):
        user = users.get_current_user()
        profile = models.Profile(key_name=user.user_id(), email=user.email(), weekly_email=True)
        profile.first_name = self.request.get('firstname')
        profile.last_name = self.request.get('lastname')
        profile.timezone = self.request.get('timezone')
        profile.get_nickname
        profile.put()

        # see if there are any pending team invitations for this email address
        invitations = models.Invitation.pending_for_email(user.email())
        if invitations is not None:
            for invite in invitations:
                # add a reference to newly created profile on the invite
                # so that profile.pending_invitation_set will return
                # these pending invitations in the sidebar
                invite.invitee_profile = profile
                invite.put()
        
        if profile.first_name is not None:
            first_name = profile.first_name
        personalized_html_message = welcome_form % {"username": first_name}
        
        welcome_message = mail.EmailMessage(
            sender = 'SNPTZ <weekly@snptz.com>',
            to = user.email(),
            reply_to = 'SNPTZ <mail@snptzapp.appspotmail.com>',
            subject = 'Welcome to SNPTZ!',
            body = 'test',
            html = personalized_html_message)
        welcome_message.send()
        
        self.redirect("/")

welcome_form = '''
<img src="http://www.snptz.com/static/logoMed.png" width="174" height="50" alt="SNPTZ">
<p>Hi %(username)s!</p>
<p>Welcome to SNPTZ!</p>
<p>
Please hit reply and tell us a few things you're going to work on this week in the space below (reply inline).
Or visit <a href="http://www.snptz.com">snptz.com</a>.  Each week, we'll follow up so you can reflect on your progress --
and share your plans with your esteemed colleagues (if they use SNPTZ too).
</p>
--~--~--~--~--~--~--~--~--~--~--~--~--~--~<br/>
WHAT'RE YOU GOING TO DO THIS WEEK?<br/>
--~--~--~--~--~--~--~--~--~--~--~--~--~--~<br/>
<br/>
REPLACE ME!<br/>
REPLACE ME!<br/>
REPLACE ME!<br/>
REPLACE ME!<br/>
<br/>
--~--~--~--~--~--~--~--~--~--~--~--~--~--~<br/>
(list any number of tasks above this line)<br/>
'''

def doRender(handler, tname, values = { }):
    temp = os.path.join(
       os.path.dirname(__file__),
       'templates/' + tname)
    if not os.path.isfile(temp):
        return False

    # Make a copy of the dictionary and add the path
    newval = dict(values)
    newval['path'] = handler.request.path

    outstr = template.render(temp, newval)
    handler.response.out.write(outstr)
    return True
    
application = webapp.WSGIApplication([
   ('/signup', Signup)],
   debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
import os
import models
import logging

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        logging.info("the user is %s" % (user))
        
        if user is None:
            loginURL = users.create_login_url("/")
            doRender(self, 'index.html', {'loginURL' : loginURL})
            return
            
        profile = models.Profile.get_by_key_name(user.user_id())
        if profile is None:
            # TODO This should be taken out and replaced with a signup step
            # need this here for now to prevent endless redirects to login page
            # if user's profile doesn't exist yet
            profile = models.Profile(key_name=user.user_id(), email=user.email(), weekly_email=True)
            profile.put()
            loginURL = users.create_login_url("/")
            doRender(self, 'index.html', {'loginURL' : loginURL})
            return
            
        else:
            renderMainPage(self, "main")

class Info(webapp.RequestHandler):
    def get(self):
        renderMainPage(self, "info")
        
class Settings(webapp.RequestHandler):
    def get(self):
        renderMainPage(self, "settings")

    def post(self):
        user = users.get_current_user()
        profile = models.Profile.get_by_key_name(user.user_id())

        profile.first_name = self.request.get('firstname')
        profile.last_name = self.request.get('lastname')
        profile.weekly_email = self.request.get('weeklyEmailsToggle', '').lower() in ['true', 'yes', 't', '1', 'on', 'checked']
        profile.timezone = self.request.get('timezone')
        profile.put()
        self.redirect('/settings')

def renderMainPage(handler, selectedPage):
    current_page = selectedPage;
    user = users.get_current_user()
    profile = models.Profile.get_by_key_name(user.user_id())
    
    # TODO This should be taken out and replaced with a signup step
    if profile is None:
        profile = models.Profile(key_name=user.user_id(), email=user.email(), weekly_email=True)
        profile.put()

    logoutURL = users.create_logout_url("/")

    teams = [m.team for m in profile.membership_set]

    doRender(handler, 'main.html', {'logoutURL' : logoutURL,
                                    "profile": profile,
                                    "teams": teams,
                                    'current_page' : current_page})
                                 
# A helper to do the rendering and to add the necessary
# variables for the _base.htm template
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
   ('/', MainPage),
   ('/info', Info),
   ('/settings', Settings)],
   debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

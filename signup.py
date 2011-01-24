#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os
import logging
from google.appengine.api import users
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
                
        self.redirect("/")

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

#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import os
import models
from google.appengine.ext.webapp import template
from google.appengine.ext import db

class Settings(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        profile = models.Profile.get_by_key_name(user.user_id())
        logoutURL = users.create_logout_url("/")    
        
        doRender(self, 'settings.html', {'email' : profile.email,
                                         'firstName' : profile.first_name,
                                         'lastName' : profile.last_name,
                                         'logoutURL' : logoutURL})

    def post(self):
        user = users.get_current_user()
        profile = models.Profile.get_by_key_name(user.user_id())
        logoutURL = users.create_logout_url("/")
        
        profile.first_name = self.request.get('firstname')
        profile.last_name = self.request.get('lastname')
        profile.put()
        self.redirect('/settings')

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
   ('/settings', Settings)],
   debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

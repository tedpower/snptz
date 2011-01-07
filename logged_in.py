#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import os
import models
from google.appengine.ext.webapp import template
from google.appengine.ext import db

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        # check to see if the user is already in the datastore
        que = db.Query(models.User)
        que = que.filter('googUser =',user.email())
        results = que.fetch(limit=1)

        # if not, add the user to the datastore
        if len(results) == 0 :
            newUser = models.User(googUser=user.email())
            newUser.put()
            user = newUser
            # self.redirect('/')
        else:
            # we want to deal with our models.User class
            # rather than the object returned by the get_current_user api call
            user = results[0]

        logoutURL = users.create_logout_url("/")

        this_week = user.this_weeks_taskweek
        last_past = user.last_past_taskweek
        all_other_past = user.all_other_past_taskweeks

        doRender(self, 'main.html', {'userNickname' : user.googUser,
            'logoutURL' : logoutURL, 'this_week' : this_week,
            'last_past' : last_past, 'all_other_past' : all_other_past})

# A helper to do the rendering and to add the necessary
# variables for the _base.htm template
def doRender(handler, tname, values = { }):
    temp = os.path.join(
       os.path.dirname(__file__),
       'templates/' + tname)
    if not os.path.isfile(temp):
        return False

    # Make a copy of the dictionary and add the path and user
    newval = dict(values)
    newval['path'] = handler.request.path

    outstr = template.render(temp, newval)
    handler.response.out.write(outstr)
    return True

application = webapp.WSGIApplication([
   ('/main', MainPage)],
   debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

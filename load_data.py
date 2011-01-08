#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os
import logging
import datetime

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import models

class LoadData(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        mister = models.Profile.get_by_key_name(user.user_id())
        if mister is None:
            mister = models.Profile(key_name=user.user_id(), email=user.email())
            mister.put()


        one = models.TaskWeek(user=mister, created=datetime.datetime(2011, 1, 3),
                optimistic=['eat', 'pray', 'love'])
        one.put()

        two = models.TaskWeek(user=mister, created=datetime.datetime(2010, 12, 27),
                optimistic=['moderation', 'scrabble', 'be merry'],
                realistic=['champagne', 'friends', 'drinking'])
        two.put()

        three = models.TaskWeek(user=mister, created=datetime.datetime(2010, 12, 20),
                optimistic=['eat', 'drink', 'be merry'],
                realistic=['family', 'friends', 'drinking'])
        three.put()

        four = models.TaskWeek(user=mister, created=datetime.datetime(2010, 12, 13),
                optimistic=['productivity', 'work', 'eagerness'],
                realistic=['lazy', 'sick', 'shopping'])
        four.put()

        self.redirect('/main')

application = webapp.WSGIApplication([
   ('/fixtures', LoadData)],
   debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

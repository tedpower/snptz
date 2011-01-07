#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
import logging
import datetime

# TODO move to separate file?
# subclasses of datetime.tzinfo to define timezones we want to use
# and how they relate to UTC
class UtcTzinfo(datetime.tzinfo):
    def utcoffset(self, dt): return datetime.timedelta(0)
    def dst(self, dt): return datetime.timedelta(0)
    def tzname(self, dt): return 'UTC'
    def olsen_name(self): return 'UTC'

class EstTzinfo(datetime.tzinfo):
    def utcoffset(self, dt): return datetime.timedelta(hours=-5)
    def dst(self, dt): return datetime.timedelta(0)
    def tzname(self, dt): return 'EST+05EDT'
    def olsen_name(self): return 'US/Eastern'

class PstTzinfo(datetime.tzinfo):
    def utcoffset(self, dt): return datetime.timedelta(hours=-8)
    def dst(self, dt): return datetime.timedelta(0)
    def tzname(self, dt): return 'PST+08PDT'
    def olsen_name(self): return 'US/Pacific'

# dictionary of instances of our tzinfo subclasses
TZINFOS = {
  'utc': UtcTzinfo(),
  'est': EstTzinfo(),
  'pst': PstTzinfo(),
}

# A Model for a message
class Message(db.Model):
    sender = db.StringProperty()
    userRef = db.ReferenceProperty()
    body = db.TextProperty()
    created = db.DateTimeProperty(auto_now_add=True)

    # the property decorator allows a method to be called as if it were
    # a read-only attribute of Message
    # (e.g., that_message.my_property rather than that_message.my_property() )
    # this allows us to use created_est within a django template just like
    # any of the Message attributes
    @property
    def created_est(self):
        # datetime stored in created is timezone naive
        created_utc_naive = self.created
        # make it timezone aware -- datetime.datetime.now() on google appengine
        # will always be in UTC, so add our UtzTzinfo class as its tzinfo attribute
        created_utc_aware = created_utc_naive.replace(tzinfo=TZINFOS['utc'])
        # use the astimezone method to convert the timezone aware datetime
        # to EST timezone (as defined by our EstTzinfo class)
        return created_utc_aware.astimezone(TZINFOS['est'])


# User model
class User(db.Model):
    # TODO rename googUser to email?
    googUser = db.StringProperty()
    first_name = db.StringProperty()
    last_name = db.StringProperty()

    @classmethod
    def find_by_email(klass, str):
        # start with all users
        user_query = klass.all()
        # filter users by email equalling str
        user_query.filter("googUser = ", str)
        # fetch and return one match (or None)
        return user_query.fetch(1)[0]

    @property
    def this_weeks_taskweek(self):
        # when are we?
        now_now = datetime.datetime.now()
        # get year, week number (1-52 or 53), and day number (1-7) for today
        year, week_num, day_num = now_now.date().isocalendar()
        # get all of this user's taskweeks
        taskweeks = self.taskweek_set
        # limit these taskweeks to those from this year & week
        taskweek = [tw for tw in taskweeks if tw.year_and_week_num == (year, week_num)]
        if len(taskweek) == 1:
            # if there is exactly one, return it
            return taskweek[0]
        if len(taskweek) == 0:
            # if there are none, create one
            created_tw = TaskWeek(user=self)
            created_tw.put()
            return created_tw
        else:
            # TODO if there are more than one ...
            return "WTF"

    @property
    def last_past_taskweek(self):
        # when are we?
        now_now = datetime.datetime.now()
        # get year, week number (1-52 or 53), and day number (1-7) for today
        year, week_num, day_num = now_now.date().isocalendar()
        # get all of this user's taskweeks
        last_past_q = TaskWeek.all()
        last_past_q.order("-created")
        last_past_q.filter("user = ", self)
        last_past = last_past_q.fetch(1)
        if len(last_past) == 1:
            return last_past
        else:
            return None


class TaskWeek(db.Model):
    user = db.ReferenceProperty(User)
    created = db.DateTimeProperty(auto_now_add=True)
    # what they hoped to accomplish
    optimistic = db.StringListProperty()
    # what they actually accomplished
    realistic = db.StringListProperty()

    @property
    def year_and_week_num(self):
        # get year, week number (1-52 or 53), and day number (1-7) for created date
        year, week_num, day_num = self.created.date().isocalendar()
        # return a tuple of year and week number
        return (year, week_num)

#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
import logging
import datetime
from timezones import *

# dictionary of instances of our tzinfo subclasses
# as defined in timezones.py
# these are the values that should be used
# in the dropdown on /templates/settings.html
TZINFOS = {
  'utc': UtcTzinfo(),
  'est': EstTzinfo(),
  'cst': CstTzinfo(),
  'mst': MstTzinfo(),
  'pst': PstTzinfo(),
}

def year_and_week_num_of(dt):
    # get year, week number (1-52 or 53), and day number (1-7) for given datetime
    year, week_num, day_num = dt.date().isocalendar()
    # return a tuple of year and week number
    return (year, week_num)

class Team(db.Model):
    name = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)

    @property
    def emails_of_members(self):
        str_list = ""
        for p in self.membership_set:
            str_list = str_list + (p.profile.email) + ', '
        return str_list

    @classmethod
    def find_by_name(klass, str):
        team_q = klass.all()
        team_q.filter("name = ", str)
        matches = team_q.fetch(1)
        if len(matches) != 0:
            return matches[0]
        else:
            return None

class Profile(db.Model):
    user = db.UserProperty(auto_current_user_add=True)
    # XXX note that user.email() could return a different email
    # address than self.email if the user changes their google
    # account's email handle
    email = db.EmailProperty()
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    weekly_email = db.BooleanProperty()
    timezone = db.StringProperty()

    @classmethod
    def find_by_email(klass, str):
        # start with all users
        user_query = klass.all()
        # filter users by email equalling str
        user_query.filter("email = ", str)
        # fetch and return one match (or None)
        matches = user_query.fetch(1)
        if len(matches) != 0:
            return matches[0]
        else:
            return None

    @property
    def nickname(self):
        return self.user.nickname()

    @property
    def this_weeks_taskweek(self):
        # TODO rename to get_or_create_...?
        # when are we?
        now_now = datetime.datetime.now()
        # get all of this user's taskweeks
        taskweeks = self.taskweek_set

        if taskweeks.count() == 0:
            # if there are none, create one
            created_tw = TaskWeek(profile=self)
            created_tw.created=now_now
            created_tw.put()
            return created_tw

        logging.info(taskweeks)
        # otherwise limit these taskweeks to those from this year & week
        taskweek = [tw for tw in taskweeks
                if year_and_week_num_of(tw.created) == year_and_week_num_of(now_now)]
        logging.info(taskweek)
        if len(taskweek) == 1:
            # if there is exactly one, return it
            return taskweek[0]
        else:
            # TODO if there are more than one ...
            logging.info("OOPS. USER HAS MORE THAN ONE TASKWEEK FOR THIS WEEK")
            return "WTF"

    @property
    def last_past_taskweek(self):
        last_past_q = TaskWeek.all()
        # order by most recent first
        last_past_q.order("-created")
        # limit to this user's taskweeks
        last_past_q.filter("profile = ", self)
        # fetch the most recent two
        last_past_res = last_past_q.fetch(2)
        # don't include any from this week
        if len(last_past_res) > 0:
            last_past = [tw for tw in last_past_res
                if year_and_week_num_of(tw.created) != year_and_week_num_of(datetime.datetime.now())]
            if len(last_past) > 0:
                return last_past[0]
        return None

    @property
    def all_other_past_taskweeks(self):
        past_q = TaskWeek.all()
        # order by most recent first
        past_q.order("-created")
        # limit to this user's taskweeks
        past_q.filter("profile = ", self)
        # fetch the most recent dozen
        all_past = past_q.fetch(12)
        # exclude this week's and last past week's taskweeks,
        # bc they are handled separately
        exclude = []

        # add (year, week_num) tuple of this week to exclude list
        exclude.append(year_and_week_num_of(datetime.datetime.now()))

        last_past_taskweek = self.last_past_taskweek
        if last_past_taskweek is not None:
            # add (year, week_num) tuple of last_past_taskweek to exclude list
            exclude.append(year_and_week_num_of(self.last_past_taskweek.created))

        # return list of taskweeks that are not excluded
        return [tw for tw in all_past if year_and_week_num_of(tw.created) not in exclude]

    @property
    def esteemed_colleagues(self):
        teams = [m.team for m in self.membership_set]
        if len(teams) == 0:
            return None
        esteemed_colleagues = []
        for team in teams:
            for mem in team.membership_set:
                if mem.profile.email != self.email:
                    if mem.profile not in esteemed_colleagues:
                        esteemed_colleagues.append(mem.profile)
        return esteemed_colleagues


class TaskWeek(db.Model):
    profile = db.ReferenceProperty(Profile)
    #created = db.DateTimeProperty(auto_now_add=True)
    created = db.DateTimeProperty()
    # what they hoped to accomplish
    optimistic = db.StringListProperty()
    # what they actually accomplished
    realistic = db.StringListProperty()

# A Model for a received email message
class Message(db.Model):
    sender = db.StringProperty()
    userRef = db.ReferenceProperty(Profile)
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

class Membership(db.Model):
    profile = db.ReferenceProperty(Profile)
    team = db.ReferenceProperty(Team)

    @classmethod
    def find_by_profile_and_team(klass, prof, t):
        # start with all users
        mem_q = klass.all()
        mem_q.filter("profile = ", prof)
        mem_q.filter("team = ", t)
        # fetch and return one match (or None)
        matches = mem_q.fetch(1)
        if len(matches) != 0:
            return matches[0]
        else:
            return None

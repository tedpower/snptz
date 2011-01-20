#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from datetime import datetime, timedelta
import logging
import re
import datetime
from timezones import *
import helpers


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
    slug = db.StringProperty()
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

    @classmethod
    def find_by_slug(klass, str):
        team_q = klass.all()
        team_q.filter("slug = ", str)
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
    nickname = db.StringProperty()
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

    @classmethod
    def find_by_nickname(klass, str):
        # start with all users
        user_query = klass.all()
        # filter users by email equalling str
        user_query.filter("nickname = ", str)
        # fetch and return one match (or None)
        matches = user_query.fetch(1)
        if len(matches) != 0:
            return matches[0]
        else:
            return None

    @property
    def get_nickname(self):
        if self.nickname is not None:
            return self.nickname
        else:
            nick = self.user.nickname()
            # self.user.nickname() will return the whole email address
            # for dev users and gmail for their domain users
            ats = nick.count("@")
            if ats > 0:
                no_at = nick.replace("@", "-")
                self.nickname = no_at
            else:
                self.nickname = nick
            # TODO enforce uniqueness of nickname!
            self.put()
            return self.nickname

    @property
    def get_key(self):
        return self.key()

    @property
    def name(self):
        if (self.first_name and self.last_name) is not None:
            return "%s %s" % (self.first_name, self.last_name)
        else:
            return self.nickname

    @property
    def this_weeks_tw(self):
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

        # otherwise limit these taskweeks to those from this year & week
        taskweek = [tw for tw in taskweeks
                if year_and_week_num_of(tw.created) == year_and_week_num_of(now_now)]

        if len(taskweek) == 1:
            # if there is exactly one, return it
            return taskweek[0]
        elif len(taskweek) == 0:
            # if there are none, create one
            created_tw = TaskWeek(profile=self)
            created_tw.created=now_now
            created_tw.put()
            return created_tw
        else:
            # TODO if there are more than one ...
            logging.info("OOPS. USER HAS MORE THAN ONE TASKWEEK FOR THIS WEEK")
            return "WTF"

    @property
    def freshest_taskweek(self):
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

        # freshest_taskweek = self.freshest_taskweek
        # if freshest_taskweek is not None:
        #     # add (year, week_num) tuple of freshest_taskweek to exclude list
        #     exclude.append(year_and_week_num_of(self.freshest_taskweek.created))

        # return list of taskweeks that are not excluded
        results = [tw for tw in all_past if year_and_week_num_of(tw.created) not in exclude]
        
        if len(results) == 0:
            return None
        else:
            return results

    @property
    def esteemed_colleagues(self):
        # get all of the teams this profile is a member of
        teams = [m.team for m in self.membership_set]
        if len(teams) == 0:
            return None
        esteemed_colleagues = []
        for team in teams:
            # loop through all the members of all the teams
            for mem in team.membership_set:
                if mem.profile.email != self.email:
                    # avoid adding self (by checking if emails are equal)
                    if mem.profile not in esteemed_colleagues:
                        # add to esteemed_colleagues if the profile
                        # is not already there (avoid duplicates)
                        esteemed_colleagues.append(mem.profile)
        return esteemed_colleagues


class TaskWeek(db.Model):
    profile = db.ReferenceProperty(Profile)
    # TODO XXX turn auto_now_add back on for production and stop
    # setting it manually in receive_email.py
    #created = db.DateTimeProperty(auto_now_add=True)
    created = db.DateTimeProperty()
    modified = db.DateTimeProperty(auto_now=True)

    def get_or_create_tasklist(self, tl_type):
        assert tl_type in ["realistic", "optimistic"]
        looking_for = True if tl_type == "optimistic" else False
        matches = [tl for tl in self.tasklist_set if tl.optimistic == looking_for]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) == 0:
            tl = TaskList(taskweek=self, optimistic=looking_for)
            tl.put()
            return tl
        else:
            # TODO do something...
            logging.info("WTF")
            logging.info(len(matches))
            pass

    def update_tasklist_tasks(self, tl_type, list_of_tasks):
        ''' Updates Tasks (and TaskLists) associated with a
            TaskWeek. Given a type (realistic or optimistic) and
            a list of tasks (with optional tags), this method
            gets/edits or creates appropriate TaskList and Task
            records referenced to this TaskWeek. If there is already
            a TaskList and Tasks of tl_type, the existing Tasks will
            be deleted before the new ones are created.

            Other than perhaps getting/displaying, TaskList and Task records
            should not be modified by other callers.'''
        assert tl_type in ["realistic", "optimistic"]
        tasklist = self.get_or_create_tasklist(tl_type)
        # gather any tasks that belong to this list
        tasks_to_replace = tasklist.task_set
        if tasks_to_replace.count() > 0:
            # if any tasks exist, delete them
            for old_task in tasks_to_replace:
                old_task.delete()
        for t in list_of_tasks:
            # create a Task for each of the items pulled from
            # the email and add a reference to the tasklist
            task = Task(tasklist=tasklist)
            task_text, tag_list = helpers.extract_tags(t)
            task.text = task_text
            if tag_list is not None:
                task.tags = tag_list
            task.put()
        tasklist.put()
        self.put()
        # TODO return something more useful?
        return True

    def _tasklist_tasks(self, tl_type):
        assert tl_type in ["realistic", "optimistic"]
        looking_for = True if tl_type == "optimistic" else False
        matches = [tl for tl in self.tasklist_set if tl.optimistic == looking_for]
        if len(matches) > 0:
            tasks = matches[0].task_set
            if tasks.count() > 0:
                return [t.text for t in tasks]
        else:
            return []

    @property
    def optimistic(self):
        return self._tasklist_tasks("optimistic")

    @property
    def realistic(self):
        return self._tasklist_tasks("realistic")

    @property
    def optimistic_as_str(self):
        return "\n".join(self.optimistic)

    @property
    def realistic_as_str(self):
        return "\n".join(self.realistic)
    
    def _tasklist_as_tuples(self, tl_type):
        assert tl_type in ["realistic", "optimistic"]
        looking_for = True if tl_type == "optimistic" else False
        matches = [tl for tl in self.tasklist_set if tl.optimistic == looking_for]
        if len(matches) > 0:
            tasks = matches[0].task_set
            if tasks.count() > 0:
                tasks_as_tuples = []
                for t in tasks:
                    tags = t.tags
                    if len(tags) > 0:
                        tasks_as_tuples.append((t.text, tuple(tags)))
                    else:
                        tasks_as_tuples.append((t.text, tuple()))
                return tasks_as_tuples
        else:
            return []

    @property
    def optimistic_as_tuples(self):
        return self._tasklist_as_tuples("optimistic")

    @property
    def realistic_as_tuples(self):
        return self._tasklist_as_tuples("realistic")

    # Takes the created date and finds the monday of the containing week
    @property
    def get_mon(self):
        return self.created + timedelta(days = -self.created.weekday())

    # Takes the created date and finds the sunday of the containing week
    @property
    def get_sun(self):
        return self.created + timedelta(days = (6 -self.created.weekday()))

    @property
    def get_key(self):
        return self.key()

class TaskList(db.Model):
    # TaskList is either of type 'optimistic' or 'realistic',
    # so if optimistic is false, assume it is of type realistic
    optimistic = db.BooleanProperty()
    taskweek = db.ReferenceProperty(TaskWeek)

class Task(db.Model):
    text = db.StringProperty()
    tags = db.StringListProperty()
    tasklist = db.ReferenceProperty(TaskList)
    created = db.DateTimeProperty(auto_now_add=True)

# A Model for a received email message
class Message(db.Model):
    sender = db.StringProperty()
    userRef = db.ReferenceProperty(Profile)
    body = db.TextProperty()
    created = db.DateTimeProperty(auto_now_add=True)

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

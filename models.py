#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.ext import db
from datetime import datetime, timedelta
import logging
import re
import hashlib
import datetime
from timezones import *


# slightly modified method cribbed from django
# (django/template/defaultfilters.py)
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return (re.sub('[-\s]+', '-', value))

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
        ''' Return a list of profiles for users that share
            membership in this user's teams (not including this user).'''
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
    # what they hoped to accomplish
    optimistic = db.StringListProperty()
    # what they actually accomplished
    realistic = db.StringListProperty()

    @property
    def optimistic_as_str(self):
        return "\n".join(self.optimistic)

    @property
    def realistic_as_str(self):
        return "\n".join(self.realistic)
    
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

class Invitation(db.Model):
    team = db.ReferenceProperty(Team)
    inviter = db.ReferenceProperty(Profile, 
        collection_name="sent_invitation_set")
    invitee_email = db.EmailProperty()

    invitee_profile = db.ReferenceProperty(Profile,
        collection_name="pending_invitation_set")

    @property
    def get_key(self):
        return self.key()

    @classmethod
    def pending_for_email(klass, str):
        # start with all users
        query = klass.all()
        query.filter("invitee_email = ", str)
        # fetch and return matches
        matches = query.fetch(50)
        if len(matches) != 0:
            return matches
        else:
            return None

    @classmethod
    def invite_colleague(klass, team, inviter, invitee_email):
        # see if there are any outstanding invitations for this invitee
        pending_for_invitee = klass.pending_for_email(invitee_email)
        if pending_for_invitee is not None:
            if team.key() in (i.team.key() for i in pending_for_invitee):
                # return a warning if there is already a pending invitation
                # for this team+email (and do not create invitation)
                return "'%s' has already been invited to '%s'" % (invitee_email, team.name)
        invitation = klass(team=team, inviter=inviter, invitee_email=invitee_email)
        invitee_profile = Profile.find_by_email(invitee_email)
        if invitee_profile is not None:
            if team.key() in (m.team.key() for m in invitee_profile.membership_set):
                # return a warning if invitee is already a member
                # (and do not create invitation)
                return "'%s' is already a member of '%s'" % (invitee_email, team.name)
            invitation.invitee_profile = invitee_profile
        invitation.put()

        team_invite_template = '''
Hi,

Your esteemed colleague %(inviter)s has invited you
to join the '%(team)s' team on SNPTZ.

Visit http://snptz.com to accept the invitation.

Thanks!
SNPTZ
'''
        team_invite_body = team_invite_template % {"inviter": inviter.first_name, "team": team.name}

        message = mail.EmailMessage(
            sender='SNPTZ <weekly@snptz.com>',
            to=invitee_email,
            reply_to='SNPTZ <mail@snptzapp.appspotmail.com>',
            subject="SNPTZ: %s has invited you to join '%s' team" % (inviter.first_name, team.name),
            body=team_invite_body)

        message.send()
        return invitation

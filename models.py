#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.ext import db
from datetime import datetime, timedelta
import logging
import hashlib
import re
import hashlib
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

    # list of Network keys of which user is a confirmed affiliate
    networks = db.ListProperty(db.Key)

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
        return []

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

    @property
    def owner(self):
        return self.tasklist.taskweek.profile

    @classmethod
    def tagged_with_intersection(klass, tag_list, network_key_list=None):
        ''' Returns tasks tagged with ALL of the provided tags in tag_list'''
        query_str = "WHERE tags = '%s'" % (tag_list[0])
        if len(tag_list) > 1:
            for tag in tag_list[1:]:
                query_str = query_str + "AND tags = '%s'" % (tag)
        tag_q = klass.gql(query_str)
        tagged_tasks = tag_q.fetch(100)
        if network_key_list is not None:
            networks = set(network_key_list)
            # limit matching tasks (that are tagged with all given tags) to
            # those whose owner belongs to one of the given networks
            visible_to_user = [t for t in tagged_tasks if len(set(t.owner.networks).intersection(networks)) > 0]
            return visible_to_user
        # if no network_key_list is provided, return all tasks tagged with
        # given tags irregardless of owner's network affiliation
        # TODO XXX probably should return None instead?!
        return tagged_tasks

    @classmethod
    def tagged_with_union(klass, tag_list, network_key_list=None):
        ''' Returns tasks tagged with at least ONE of the provided tags in tag_list'''
        tag_q = klass.all()
        tag_q.filter("tags IN", tag_list)
        tag_q.order("-created")
        tagged_tasks = tag_q.fetch(100)
        if network_key_list is not None:
            networks = set(network_key_list)
            # limit matching tasks (that are tagged with one of the given tags) to
            # those whose owner belongs to one of the given networks
            visible_to_user = [t for t in tagged_tasks if len(set(t.owner.networks).intersection(networks)) > 0]
            return visible_to_user
        # if no network_key_list is provided, return all tasks tagged with
        # a given tag irregardless of owner's network affiliation
        # TODO XXX probably should return None instead?!
        return tagged_tasks

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

class Network(db.Model):
    name = db.StringProperty()
    slug = db.StringProperty()
    # email domain used to verify affiliated profiles
    # e.g., '@snptz.com'
    email_domain = db.StringProperty()

    @classmethod
    def find_by_slug(klass, str):
        q = klass.all()
        q.filter("slug = ", str)
        matches = q.fetch(1)
        if len(matches) != 0:
            return matches[0]
        else:
            return None

    @classmethod
    def find_by_domain(klass, str):
        q = klass.all()
        q.filter("email_domain = ", str)
        matches = q.fetch(1)
        if len(matches) != 0:
            return matches[0]
        else:
            return None


class PendingConfirmation(db.Model):
    email_address = db.EmailProperty()
    profile = db.ReferenceProperty(Profile)
    network = db.ReferenceProperty(Network)
    secret_code = db.StringProperty()
    expires_at = db.DateTimeProperty()

    @classmethod
    def find_by_code(klass, str):
        q = klass.all()
        q.filter("secret_code = ", str)
        matches = q.fetch(1)
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
    def send_confirmation(klass, email, profile, network):
        new_PC = klass(email_address=email, profile=profile, network=network)
        # generate hash unique to this email + network
        secret = hashlib.sha224(email + network.slug).hexdigest()
        new_PC.secret_code = secret
        # set PC to expire in one week
        new_PC.expires_at = datetime.datetime.now() + timedelta(7)
        new_PC.put()

        conf_email_template = '''
Hi %(username)s,

Please click on the link below to confirm
your affiliation with %(network)s:

%(link)s

Thanks!
SNPTZ
        '''
        secret_link = "http://snptz.com/confirm/%s" % (secret)
        conf_email_body = conf_email_template % {"username": profile.first_name,\
            "network": network.name, "link": secret_link}

        message = mail.EmailMessage(
            sender='SNPTZ <weekly@snptz.com>',
            to=email,
            reply_to='SNPTZ <mail@snptzapp.appspotmail.com>',
            subject="SNPTZ: confirm your affiliation with '%s' network" % (network.name),
            body=conf_email_body)

        message.send()
        return new_PC

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

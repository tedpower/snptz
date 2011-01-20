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
import helpers

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        
        if user is None:
            loginURL = users.create_login_url("/")
            doRender(self, 'index.html', {'loginURL' : loginURL})
            return
            
        profile = models.Profile.get_by_key_name(user.user_id())
        if profile is None:
            loginURL = users.create_login_url("/")
            doRender(self, 'index.html', {'loginURL' : loginURL})
            return
            
        else:
            renderMainPage(self, "main")

class Info(webapp.RequestHandler):
    def get(self):
        renderMainPage(self, "info")
        
class Colleague(webapp.RequestHandler):
    def get(self, nickname):
        colleague = models.Profile.find_by_nickname(nickname)
        if colleague is None:
            self.redirect("/404")
        renderMainPage(self, "colleague", colleague=colleague)

class Settings(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        profile = models.Profile.get_by_key_name(user.user_id())

        memberships = profile.membership_set
        # get a list of teams user has membership in
        memberships_teams = [m.team for m in memberships]
        # get a list of teams user does not have membership in
        other_teams = [t for t in models.Team.all() if t.key() not in [m.key() for m in memberships_teams]]

        renderMainPage(self, "settings", memberships_teams=memberships_teams,
            other_teams=other_teams)

    def post(self):
        user = users.get_current_user()
        profile = models.Profile.get_by_key_name(user.user_id())

        profile.first_name = self.request.get('firstname')
        profile.last_name = self.request.get('lastname')
        profile.weekly_email = self.request.get('weeklyEmailsToggle', '').lower() in ['true', 'yes', 't', '1', 'on', 'checked']
        profile.timezone = self.request.get('timezone')
        profile.put()
        self.response.out.write("Your settings have been saved")        

class Taskweek(webapp.RequestHandler):

    def get(self, tw_type, tw_key):
        assert (tw_type in ['realistic', 'optimistic']), "tw_type is not known: %s" % `tw_type`
        # this method expects a url formatted like:
        #   http://localhost:8080/taskweek/show/optimistic/aghzbnB0emFwcHIOCxIIVGFza1dlZWsYFww
        #   e.g.,
        #   http://mydomain/taskweek/show/(optimistic or realistic)/(taskweek.get_key)
        # and returns a little rendered template (html) ideal for loading into a page via ajax
        user = users.get_current_user()
        profile = models.Profile.get_by_key_name(user.user_id())

        # get the path for the appropriate template, based on type of taskweek
        template_path = 'templates/partials/taskweek_%s.html' % tw_type

        # find taskweek based on key provided in url
        taskweek = models.TaskWeek.get(tw_key)

        if taskweek is not None:
            # respond with rendered template
            return self.response.out.write(template.render(template_path, {'taskweek':taskweek}))

    def post(self, tw_type):
        assert (tw_type in ['realistic', 'optimistic']), "tw_type is not known: %s" % `tw_type`

        user = users.get_current_user()
        profile = models.Profile.get_by_key_name(user.user_id())

        tw_key = self.request.get('twkey')
        edited = self.request.get('twedit')
        tw_attr = tw_type

        taskweek = models.TaskWeek.get(tw_key)
        if taskweek is None:
            logging.info('OOPS. TASKWEEK FOR EDITING NOT FOUND')
            self.response.out.write("Oops. FAIL!")
        else:
            edited_as_lines = [l.strip() for l in edited.splitlines()]
            if hasattr(taskweek, tw_attr):
                setattr(taskweek, tw_attr, edited_as_lines)
            taskweek.put()
            self.response.out.write("Yay. Your tasks have been updated.")
        
class Team(webapp.RequestHandler):
    def get(self, verb, team_slug):
        assert (verb == "show"), "GET verb is not show: %s" % `verb`
        team = models.Team.find_by_slug(team_slug)
        # if team is None, give 'em a 404
        if team is None:
            self.redirect("/404")
        renderMainPage(self, "team", team=team)

    def post(self, verb, team_slug):
        assert (verb in ["new", "toggle"]), "POST verb is not supported: %s" % `verb`
        user = users.get_current_user()
        profile = models.Profile.get_by_key_name(user.user_id())
        
        if verb == "new":
            # if user is creating a new team...
            team_name = self.request.get('newteamname')
            if team_name not in [None, '', ' ']:
                # make sure it doesnt exist yet
                team = models.Team.find_by_name(team_name)
                if team is None:
                    # create new team
                    team = models.Team(name=team_name)
                    # make a slug from the supplied team name
                    team.slug = helpers.slugify(team_name)
                    team.put()
                    # create a new membership for the user
                    membership = models.Membership(team=team, profile=profile)
                    membership.put()
                    self.response.out.write("You have created and joined %s" % team.name)
                else:
                    self.response.out.write("Oops. That team name is already taken.")

        if verb == "toggle":
            # get the user's team memberships
            memberships = profile.membership_set
            # get a list of keys of the teams user has membership in
            memberships_teams_keys = [m.team.key() for m in memberships]

            team_slug = self.request.get('teamslug')
            team = models.Team.find_by_slug(team_slug)
            if team.key() not in memberships_teams_keys:
                new_member = models.Membership(team=team, profile=profile)
                new_member.put()
                self.response.out.write("You are now a member of %s" % team.name)
            else:
                if team.key() in memberships_teams_keys:
                    old_membership = models.Membership.find_by_profile_and_team(profile, team)
                    if old_membership is not None:
                        old_membership.delete()
                        self.response.out.write("You are no longer a member of %s" % team.name)

def renderMainPage(handler, selectedPage, **kwargs):
    current_page = selectedPage;
    user = users.get_current_user()
    profile = models.Profile.get_by_key_name(user.user_id())
    
    # Check to make sure the user exists
    if profile is None:
        self.redirect("/")
        return

    logoutURL = users.create_logout_url("/")

    teams = [m.team for m in profile.membership_set]

    # get the keyword argument named 'team' and set as value of variable called team
    # if there is not kwarg 'team', assign None to variable team
    team = kwargs.get('team', None)
    memberships_teams = kwargs.get('memberships_teams', None)
    other_teams = kwargs.get('other_teams', None)
    colleague = kwargs.get('colleague', None)

    doRender(handler, 'main.html', {'logoutURL' : logoutURL,
                                    "profile": profile,
                                    "teams": teams,
                                    "team": team,
                                    "memberships_teams": memberships_teams,
                                    "other_teams": other_teams,
                                    "colleague": colleague,
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
   ('/settings', Settings),
   ('/team/([^/]+)/([^/]+)', Team),
   ('/taskweek/show/([^/]+)/([^/]+)', Taskweek),
   ('/taskweek/update/([^/]+)', Taskweek),
   ('/colleague/([^/]+)', Colleague)],
   debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
import os
import models
import logging

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        logging.info("the user is %s" % (user))
        
        if user is None:
            loginURL = users.create_login_url("/")
            doRender(self, 'index.html', {'loginURL' : loginURL})
            return
            
        profile = models.Profile.get_by_key_name(user.user_id())
        if profile is None:
            # TODO This should be taken out and replaced with a signup step
            # need this here for now to prevent endless redirects to login page
            # if user's profile doesn't exist yet
            profile = models.Profile(key_name=user.user_id(), email=user.email(), weekly_email=True)
            profile.put()
            loginURL = users.create_login_url("/")
            doRender(self, 'index.html', {'loginURL' : loginURL})
            return
            
        else:
            renderMainPage(self, "main")

class Info(webapp.RequestHandler):
    def get(self):
        renderMainPage(self, "info")
        
class Team(webapp.RequestHandler):
    def get(self, team_slug):
        team = models.Team.find_by_slug(team_slug)
        # if team is None, give 'em a 404
        if team is None:
            self.redirect("/404")
        renderMainPage(self, "team", team=team)

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

        # now check the team membership settings
        
        # get the user's team memberships
        memberships = profile.membership_set
        # get a list of keys of the teams user has membership in
        memberships_teams_keys = [m.team.key() for m in memberships]
        
        for team in models.Team.all():
            logging.info(team)
            try:
                team_status = self.request.get('team-%s' % team.key())
                if team_status is not None:
                    if team_status.lower() in ['true', 'yes', 't', '1', 'on', 'checked']:
                        if team.key() not in memberships_teams_keys:
                            new_member = models.Membership(team=team, profile=profile)
                            new_member.put()
                    else:
                        if team.key() in memberships_teams_keys:
                            old_membership = models.Membership.find_by_profile_and_team(profile, team)
                            if old_membership is not None:
                                old_membership.delete()
                continue
            except Exception, e:
                logging.info(e)
        
        old_teams = self.request.get('old-team', allow_multiple=True)
        new_teams = self.request.get('new-team', allow_multiple=True)
        
        # if user is creating a new team...
        team_name = self.request.get('newteamname')
        if team_name not in [None, '', ' ']:
            # make sure it doesnt exist yet
            team = models.Team.find_by_name(team_name)
            if team is None:
                # create new team
                team = models.Team(name=team_name)
                # make a slug from the supplied team name
                team.slug = models.slugify(team_name)
                team.put()
                # create a new membership for the user
                membership = models.Membership(team=team, profile=profile)
                membership.put()
            else:
                #TODO handle case where team with this name already exists!
                pass

def renderMainPage(handler, selectedPage, **kwargs):
    current_page = selectedPage;
    user = users.get_current_user()
    profile = models.Profile.get_by_key_name(user.user_id())
    
    # TODO This should be taken out and replaced with a signup step
    if profile is None:
        profile = models.Profile(key_name=user.user_id(), email=user.email(), weekly_email=True)
        profile.put()

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
   ('/team/([^/]+)', Team),
   ('/colleague/([^/]+)', Colleague)],
   debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

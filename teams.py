#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import os
import models
import logging
from google.appengine.ext.webapp import template
from google.appengine.ext import db

class Teams(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        profile = models.Profile.get_by_key_name(user.user_id())
        team = profile.team
        logoutURL = users.create_logout_url("/")    
        
        doRender(self, 'teams.html', {'email' : profile.email,
                                        'team': team,
                                         'logoutURL' : logoutURL})

    def post(self):
        user = users.get_current_user()
        profile = models.Profile.get_by_key_name(user.user_id())

        team_name = self.request.get('teamname')
        logging.info(team_name)
        teammembers = self.request.get('teammembers')
        logging.info(teammembers)
        # split contents of teammembers into a list
        # and strip leading and/or trailing whitespace
        new_team_members = [tm.strip() for tm in teammembers.split(',')]
        logging.info(new_team_members)

        if team_name is not None:
            team = models.Team.find_by_name(team_name)
            old_team_members = []
            if team is not None:
                for t in team.profile_set:
                    old_team_members.append(str(t.email))
            if team is None:
                team = models.Team(name=team_name, owner=profile.user)
                team.put()
            new_members_added = []
            new_emails_to_invite = []
            for email in new_team_members:
                prof = models.Profile.find_by_email(email)
                if prof is not None:
                    prof.team = team
                    prof.put()
                    if email not in old_team_members:
                        # XXX this list is just for debugging
                        new_members_added.append(email)
                    if email in old_team_members:
                        # remove from old_team_members list
                        # (remaining old_team_members will be removed
                        # from this team below)
                        old_team_members.remove(email)
                else:
                    new_emails_to_invite.append(email)
            logging.info("OLD MEMBERS:")
            logging.info(old_team_members)
            logging.info("NEW ADDED:")
            logging.info(new_members_added)
            logging.info("NEW TO INVITE:")
            logging.info(new_emails_to_invite)
            # TODO email invitations to emails_to_invite!

            removed_members = []
            for email in old_team_members:
                prof = models.Profile.find_by_email(email)
                if prof is not None:
                    prof.team = None
                    prof.put()
                    removed_members.append(email)
                else:
                    logging.info("WTF")
            logging.info("REMOVED:")
            logging.info(removed_members)

        self.redirect('/teams')

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
   ('/teams', Teams)],
   debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

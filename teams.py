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
        team_members = teammembers.split(',')
        logging.info(team_members)

        if team_name is not None:
            # create and put new Team
            team = models.Team(name=team_name, owner=profile.user)
            team.put()
            members_added = []
            emails_to_invite = []
            for member in team_members:
                # strip leading and/or trailing whitespace
                email = member.strip() 
                prof = models.Profile.find_by_email(email)
                if prof is not None:
                    prof.team = team
                    prof.put()
                    members_added.append(email)
                else:
                    emails_to_invite.append(email)
            logging.info(members_added)
            logging.info(emails_to_invite)
            # TODO email invitations to emails_to_invite!

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

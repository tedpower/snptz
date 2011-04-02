#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
import os
import logging

from google.appengine.api import mail
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

        renderMainPage(self, "settings", memberships_teams=None)

    def post(self):
        user = users.get_current_user()
        profile = models.Profile.get_by_key_name(user.user_id())

        profile.first_name = self.request.get('firstname')
        profile.last_name = self.request.get('lastname')
        profile.weekly_email = self.request.get('weeklyEmailsToggle', '').lower() in ['true', 'yes', 't', '1', 'on', 'checked']
        profile.timezone = self.request.get('timezone')
        profile.put()
        self.response.out.write("Your settings have been saved")        


class Tag(webapp.RequestHandler):
    def get(self, tag):
        user = users.get_current_user()
        profile = models.Profile.get_by_key_name(user.user_id())

        tag_list = [tag]
        tasks = models.Task.tagged_with_intersection(tag_list, profile.networks)
        return self.response.out.write(template.render('templates/partials/tasks.html', {'tasks': tasks, 'tag': tag_list[0]}))

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

        params = self.request.params
        if params.has_key('twkey'):
            tw_key = params['twkey']

        tw_attr = tw_type

        taskweek = models.TaskWeek.get(tw_key)
        if taskweek is None:
            logging.info('OOPS. TASKWEEK FOR EDITING NOT FOUND')
            self.response.out.write("Oops. FAIL!")
        else:
            # lists for keeping track of tasks (task text) and tags
            tasks = list()
            tags = list()
            for k, v in params.iteritems():
                if k == 'twkey':
                    continue
                # split GET parameter keys on '-'
                id = k.split('-')
                if len(id) == 2:
                    # if id is split into two, we have a task like: 'task-4'
                    # so add a tuple to the tasks list like: (4, 'text of task 4')
                    tasks.append((id[1], v))
                if len(id) == 4:
                    # if id is split into four, we have a tag like: 'task-4-tag-2'
                    # so add a tuple to the tags list like: (4, (2, 'tag 2 text'))
                    tags.append((id[1], (id[3], v)))

            # TODO this is a dodgy hack because i didn't feel like refactoring
            # Taskweek.update_tasklist_tasks to accept tags as separate parameter
            # ... instead i'm tacking on all the tags to the text of the task
            # so its formatted as if it were coming from an email
            # e.g., 'this is my task text [one tag, two tag]'
            edited_as_lines = list()
            for task in tasks:
                line = task[1]
                line_tags = ' ['
                for tag in tags:
                    if tag[0] == task[0]:
                        if not tag[1][1] == '':
                            line_tags = line_tags + tag[1][1] + ','
                line_tags = line_tags + ']'
                line = line + line_tags
                edited_as_lines.append(line)
            taskweek.update_tasklist_tasks(tw_attr, edited_as_lines)
            taskweek.put()
            self.get(tw_type, tw_key)
            #self.response.out.write("Yay. Your tasks have been updated.")
        
class Sidebar(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        profile = models.Profile.get_by_key_name(user.user_id())
        return self.response.out.write(template.render('templates/partials/sidebar.html', {'profile':profile, 'teams':None}))

class Confirm(webapp.RequestHandler):
    def get(self, hash):
        pc = models.PendingConfirmation.find_by_code(hash)
        if pc is not None:
            network = pc.network
            # TODO check that pc has not expired!
            prof = pc.profile
            prof_nets = prof.networks
            if not network.key() in prof_nets:
                prof_nets.append(network.key())
                prof.networks = prof_nets
                prof.put()
            pc.delete()
            self.response.out.write("Thanks! Your affiliation with '%s' is confirmed" % network.name)
        else:
            self.response.out.write("Oops. PendingConfirmation not found")


class Network(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        profile = models.Profile.get_by_key_name(user.user_id())

        email = self.request.get("networkemail")
        #name = self.request.get("networkname")
        name = email.split('@')[1]

        # evan@snptz.com ==> @snptz.com
        # TODO check that we have a valid email address first!
        domain_of_email = "@" + email.split('@')[1]

        network = models.Network.find_by_domain(domain_of_email)
        if network is None:
            # create and save a new network if this is the first
            slug_from_name = helpers.slugify(name)
            network = models.Network(name=name, slug=slug_from_name, email_domain=domain_of_email)
            network.put()

        domain_of_network = network.email_domain
        if domain_of_email == domain_of_network:
            new_pc = models.PendingConfirmation.send_confirmation(email, profile, network)
            self.response.out.write("Confirmation email has been sent to %s" % email)

class SendMail(webapp.RequestHandler):
    def post(self):
        params = dict()
        params.update({'sender': self.request.get('sender')})
        params.update({'to': self.request.get('to')})
        params.update({'reply_to': self.request.get('reply_to')})
        params.update({'subject': self.request.get('subject')})
        params.update({'body': self.request.get('body')})
        params.update({'html': self.request.get('html')})
        message = mail.EmailMessage(**params)
        message.send()

    def get(self):
        post(self)

def renderMainPage(handler, selectedPage, **kwargs):
    current_page = selectedPage
    user = users.get_current_user()
    profile = models.Profile.get_by_key_name(user.user_id())
    
    # Check to make sure the user exists
    if profile is None:
        self.redirect("/")
        return

    logoutURL = users.create_logout_url("/")

    doRender(handler, 'main.html', {'logoutURL' : logoutURL,
                                    "profile": profile,
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
   ('/tag/([^/]+)', Tag),
   ('/network/join', Network),
   ('/confirm/([^/]+)', Confirm),
   ('/sidebar', Sidebar),
   ('/sendmail', SendMail),
   ('/taskweek/show/([^/]+)/([^/]+)', Taskweek),
   ('/taskweek/update/([^/]+)', Taskweek),
   ('/colleague/([^/]+)', Colleague)],
   debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

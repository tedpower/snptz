#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import os
from google.appengine.ext.webapp import template

class SplashPage(webapp.RequestHandler):
    def get(self):
        loginURL = users.create_login_url("/")
        doRender(self, 'index.html', {'loginURL' : loginURL})

# A render helper
def doRender(handler, tname, values = { }):
    temp = os.path.join(
       os.path.dirname(__file__),
       'templates/' + tname)
    if not os.path.isfile(temp):
        return False
    newval = dict(values)
    outstr = template.render(temp, newval)
    handler.response.out.write(outstr)
    return True

application = webapp.WSGIApplication([
   ('/', SplashPage)],
   debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

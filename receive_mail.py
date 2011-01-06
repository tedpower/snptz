import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp import mail_handlers
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from google.appengine.ext import db
import models
import re

class MyMailHandler(mail_handlers.InboundMailHandler):
  def receive(self, message):
    html_bodies = message.bodies('text/html')
    for content_type, body in html_bodies:
      decoded_html = body.decode()

    logging.info('Received email message from %s: %s' % (message.sender,
                                                             decoded_html))

    #clean up the email address
    pattern = re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}')
    cleanedEmail = pattern.findall(message.sender)
    logging.info('the user is %s' % (cleanedEmail[0]))
    
    #find the good bits of the email
    breakingString = "-----------------------------------------"
    start = decoded_html.find(breakingString)
    start = decoded_html.find(breakingString, start + 1)
    end = decoded_html.find(breakingString, start + 1)
    thisWeek = decoded_html[start + len(breakingString):end]
    thisWeek = thisWeek.splitlines()
    thisWeek = cleanLines(thisWeek)
    start = decoded_html.find(breakingString, end + 1)
    end = decoded_html.find(breakingString, start + 1)
    lastWeek = decoded_html[start + len(breakingString):end]
    lastWeek = lastWeek.splitlines()
    lastWeek = cleanLines(lastWeek)
    
    # find the user
    
    
    newmessage = models.Message(sender=cleanedEmail[0], thisWeek=thisWeek, lastWeek=lastWeek)
    newmessage.put()

def cleanLines(weekList):
  tempList = []
  for i in weekList:
    if (len(i) != 0) and (i.isspace() == False):
      # if(i[])
      tempList.append(i)
  return tempList


application = webapp.WSGIApplication([MyMailHandler.mapping()],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()

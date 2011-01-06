import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp import mail_handlers
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from google.appengine.ext import db
import models

class MyMailHandler(mail_handlers.InboundMailHandler):
  def receive(self, message):
    (encoding, payload) = list(message.bodies(content_type='text/plain'))[0]
    body_text = payload.decode()
    logging.info('Received email message from %s: %s' % (message.sender,
                                                             body_text))

    # find the user
    '''
    que = db.Query(models.User).User(message.sender)
    que = que.GqlQuery("SELECT * FROM models.User WHERE googUser = User(message.sender)")
    logging.info('hey there %s' % (que))
    results = que.fetch(limit=1)
    
    if len(results) == 1 : 
      newmessage = models.Message(userRef=results[0].key, body=body_text)
      newmessage.put()
    '''
    newmessage = models.Message(sender=message.sender, body=body_text)
    newmessage.put()

application = webapp.WSGIApplication([MyMailHandler.mapping()],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()

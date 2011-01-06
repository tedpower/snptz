from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
import logging
import datetime

# A Model for a message
class Message(db.Model):
  sender = db.EmailProperty()
  thisWeek = db.StringListProperty()
  lastWeek = db.StringListProperty()
  created = db.DateTimeProperty(auto_now=True)

# User model
class User(db.Model):
  googUser = db.EmailProperty()
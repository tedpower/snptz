from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
import logging
import datetime

# subclasses of datetime.tzinfo to define timezones we want to use
# and how they relate to UTC
class UtcTzinfo(datetime.tzinfo):
  def utcoffset(self, dt): return datetime.timedelta(0)
  def dst(self, dt): return datetime.timedelta(0)
  def tzname(self, dt): return 'UTC'
  def olsen_name(self): return 'UTC'

class EstTzinfo(datetime.tzinfo):
  def utcoffset(self, dt): return datetime.timedelta(hours=-5)
  def dst(self, dt): return datetime.timedelta(0)
  def tzname(self, dt): return 'EST+05EDT'
  def olsen_name(self): return 'US/Eastern'

class PstTzinfo(datetime.tzinfo):
  def utcoffset(self, dt): return datetime.timedelta(hours=-8)
  def dst(self, dt): return datetime.timedelta(0)
  def tzname(self, dt): return 'PST+08PDT'
  def olsen_name(self): return 'US/Pacific'

# dictionary of instances of our tzinfo subclasses
TZINFOS = {
  'utc': UtcTzinfo(),
  'est': EstTzinfo(),
  'pst': PstTzinfo(),
}

# A Model for a message
class Message(db.Model):
  sender = db.StringProperty()
#  userRef = db.ReferenceProperty()
  body = db.TextProperty()
  created = db.DateTimeProperty(auto_now=True)
  
  # the property decorator allows a method to be called as if it were 
  # a read-only attribute of Message
  # (e.g., that_message.my_property rather than that_message.my_property() )
  # this allows us to use created_est within a django template just like
  # any of the Message attributes
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
  
#  Since AppEngine will always give us datetime.datetime.now() in UTC,
#  we don't really need to override the put method to add tzinfo to the
#  the datetime as long as we make the datetime timezone aware before we use it
#  (like in the created_est property above)

#  def put(self):
#    self.created = datetime.datetime.now(TZINFOS['utc'])
#    db.Model.put(self)


# User model
class User(db.Model):
  googUser = db.StringProperty()

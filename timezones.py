#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

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

class CstTzinfo(datetime.tzinfo):
    def utcoffset(self, dt): return datetime.timedelta(hours=-6)
    def dst(self, dt): return datetime.timedelta(0)
    def tzname(self, dt): return 'CST+06CDT'
    def olsen_name(self): return 'US/Central'

class MstTzinfo(datetime.tzinfo):
    def utcoffset(self, dt): return datetime.timedelta(hours=-7)
    def dst(self, dt): return datetime.timedelta(0)
    def tzname(self, dt): return 'MST+07MDT'
    def olsen_name(self): return 'US/Mountain'

class PstTzinfo(datetime.tzinfo):
    def utcoffset(self, dt): return datetime.timedelta(hours=-8)
    def dst(self, dt): return datetime.timedelta(0)
    def tzname(self, dt): return 'PST+08PDT'
    def olsen_name(self): return 'US/Pacific'

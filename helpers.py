#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import re
import itertools

# slightly modified method cribbed from django
# (django/template/defaultfilters.py)
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return (re.sub('[-\s]+', '-', value))

def extract_tags(text):
    ''' Given a string, this method extracts hashtags
        and returns a tuple of string-sans-hashtags and
        a list of extracted tags.'''
    t = text
    tag_list = []
    tag_pattern = re.compile(r'\#([-A-Za-z0-9]+)')
    matches = re.findall(tag_pattern, t)
    if matches is not None:
        for match in matches:
            tag_list.append(match)
        t_no_tags, num = re.subn(tag_pattern, "", t)
        return t_no_tags.strip(), tag_list
    return t, tag_list

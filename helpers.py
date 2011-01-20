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
    ''' Given a string, this method extracts tags from within
        brackets, returning a tag-and-bracket-free string and
        a list of tags-sans-brackets.
        e.g., "[ux, android app ] work on prototype of settings interface "
            returns "work on prototype of settings interface"
                    and ['ux','android-app'] '''
    t = text
    tag_list = None
    tag_pattern = re.compile(r'\[(.*)\]')
    # search item from email for tags (stuff between [])
    matches = re.search(tag_pattern, t)
    if matches is not None:
        # if there are tags, cast the matches.groups() tuple
        # as a list, and split each list item by commas and
        # finally flatten the resulting list of lists
        raw_tags = itertools.chain.from_iterable([m.split(',')
            for m in list(matches.groups())])
        # slugify all the tags, so 'my tag ' becomes 'my-tag'
        tags = [slugify(rt) for rt in raw_tags]

        # add list of slugified tags to Task's tags property
        tag_list = tags
        tag_w_brackets_pattern = re.compile(r'\[.*\]')
        # replace tags (and enclosing brackets) with an
        # empty string, and strip any leading or trailing
        # whitespace from the task text
        text_wo_tags = tag_w_brackets_pattern.sub("", t).strip()
        # and add to Task's text property
        t = text_wo_tags
        return t, tag_list
    return t, tag_list

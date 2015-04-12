# coding: utf-8
"""
timed_config.py

Contains config helper class Until for setting config values which change at
given times. Class can be stacked to provide repeated changes.

Also includes helper functions for augmenting a flask.config.Config object to
automatically deal with Until objects
"""

from __future__ import unicode_literals

import datetime

import flask

class Until(object):
    """Config helper class to handle config values changing at set times."""

    def __init__(self, before, time, after):
        """Initialise class.

        Arguments:
            before: (any) config value to use if we are currently before |time|
            time: (datetime.datetime) when the config value should switch
            after: (any) config value to use if we are currently after |time|
        """
        self._before = before
        self._time = time
        self._after = after

    def get(self):
        """Return the appropriate value based on the current time."""
        if datetime.datetime.utcnow() < self._time:
            return self._before
        else:
            return self._after

def parse_until(value):
    """If the config value is an Until object, call its get() method."""
    if isinstance(value, Until):
        return value.get()
    else:
        return value

def augment_config(app):
    """Set up the app's config object to automatically parse Until objects."""
    old_getitem = app.config.__getitem__

    app.config.__class__ = type(
        b'Config',
        (flask.config.Config,),
        {'__getitem__': (lambda self, k: parse_until(old_getitem(k)))}
    )

    old_get = app.config.get

    app.config.get = (lambda k, d=None: parse_until(old_get(k, d)))

# coding: utf-8
"""
timed_config.py

Contains config helper class Until for setting config values which change at
given times. Class can be stacked to provide repeated changes.

Also includes helper functions for augmenting a flask.config.Config object to
automatically deal with Until objects
"""

from __future__ import unicode_literals
from __future__ import division

import datetime

import flask

class Until(object):
    """Config helper class to handle config values changing at set times."""

    def __init__(self, *args):
        """Initialise class.

        Args should be an alternating sequence of values and sequential
        datetimes.
        """
        self._values = args[::2]
        self._times = args[1::2]

        assert len(self._values) == len(self._times) + 1
        assert all(isinstance(dt, datetime.datetime) for dt in self._times)

    def get(self):
        """Return the appropriate value based on the current time."""
        left = 0
        right = len(self._times)
        now = datetime.datetime.utcnow()

        while left != right:
            mid = (left + right) // 2
            if now >= self._times[mid]:
                left = mid + 1
            else:
                right = mid

        return self._values[left]


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

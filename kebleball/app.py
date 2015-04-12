# coding: utf-8
"""Create the application object for the ticketing system.

Initialises the application object, and loads the appropriate config into it.
"""

from __future__ import unicode_literals

import flask

APP = flask.Flask('kebleball')

APP.config.from_pyfile('config/default.py')

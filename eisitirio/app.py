# coding: utf-8
"""Create the application object for the ticketing system."""

from __future__ import unicode_literals

import flask

APP = flask.Flask('eisitirio', static_folder=None)

APP.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

APP.jinja_env.trim_blocks = True
APP.jinja_env.lstrip_blocks = True

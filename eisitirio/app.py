# coding: utf-8
"""Create the application object for the ticketing system."""

from __future__ import unicode_literals

import flask

APP = flask.Flask('eisitirio')

APP.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

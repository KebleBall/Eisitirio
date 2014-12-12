# coding: utf-8
"""Create the application object for the ticketing system.

Initialises the application object, and loads the appropriate config into it.
"""
import flask

APP = flask.Flask(__name__)

APP.config.from_pyfile('config/default.py')

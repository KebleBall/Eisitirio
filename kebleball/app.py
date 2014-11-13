# coding: utf-8
"""Create the application object for the ticketing system.

Initialises the application object, and loads the appropriate config into it.
"""

import os

from flask import Flask

APP = Flask(__name__)

APP.config.from_pyfile('config/default.py')
APP.config.from_pyfile('config/development.py')

if 'KEBLE_BALL_ENV' in os.environ:
    if os.environ['KEBLE_BALL_ENV'] == 'PRODUCTION':
        APP.config.from_pyfile('config/production.py')
    elif os.environ['KEBLE_BALL_ENV'] == 'STAGING':
        APP.config.from_pyfile('config/staging.py')

# coding: utf-8
"""WSGI wrapper for the Keble Ball Ticketing System."""

from __future__ import unicode_literals

import os
import site
import sys

ROOT_DIR = os.path.realpath(__file__).replace('/wsgi.py', '')
VENV_DIR = os.path.dirname(ROOT_DIR)

site.addsitedir(os.path.join(VENV_DIR, 'lib/python2.7/site-packages/'))
sys.path.append(ROOT_DIR)

from newrelic import agent

from kebleball import app

APP = app.APP

agent.initialize(os.path.join(VENV_DIR, 'newrelic.ini'))

@agent.wsgi_application()
def application(req_environ, start_response):
    """Wrapper around actual application to load config based on environment."""
    if 'KEBLE_BALL_ENV' in req_environ:
        if req_environ['KEBLE_BALL_ENV'] == 'DEVELOPMENT':
            APP.config.from_pyfile('config/development.py')
            return APP(req_environ, start_response)
        elif req_environ['KEBLE_BALL_ENV'] == 'STAGING':
            APP.config.from_pyfile('config/staging.py')
            return APP(req_environ, start_response)
        elif req_environ['KEBLE_BALL_ENV'] == 'PRODUCTION':
            APP.config.from_pyfile('config/production.py')
            return APP(req_environ, start_response)
    else:
        return APP(req_environ, start_response)

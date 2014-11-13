# coding: utf-8
"""WSGI wrapper for the Keble Ball Ticketing System."""

import os
import site
import sys

site.addsitedir('/var/www/flask_kebleball/lib/python2.7/site-packages/')
sys.path.append(os.path.realpath(__file__).replace('/wsgi.py', ''))

import newrelic.agent

import kebleball

newrelic.agent.initialize('/var/www/flask_kebleball/newrelic.ini')

APP = kebleball.APP

@newrelic.agent.wsgi_application()
def application(req_environ, start_response):
    """Wrapper around actual application to load config based on environment."""
    if 'KEBLE_BALL_ENV' in req_environ:
        if req_environ['KEBLE_BALL_ENV'] == 'STAGING':
            APP.config.from_pyfile('config/staging.py')
            return APP(req_environ, start_response)
        elif req_environ['KEBLE_BALL_ENV'] == 'PRODUCTION':
            APP.config.from_pyfile('config/production.py')
            return APP(req_environ, start_response)
    else:
        return APP(req_environ, start_response)

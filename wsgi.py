# coding: utf-8
"""WSGI wrapper for Eisitirio."""

from __future__ import unicode_literals

import logging
import os
import site
import sys

ROOT_DIR = os.path.realpath(__file__).replace('/wsgi.py', '')
VENV_DIR = os.path.dirname(ROOT_DIR)

site.addsitedir(os.path.join(VENV_DIR, 'lib/python2.7/site-packages/'))
sys.path.append(ROOT_DIR)

from newrelic import agent

from eisitirio import app
from eisitirio import system # pylint: disable=unused-import

APP = app.APP

agent.initialize(os.path.join(VENV_DIR, 'newrelic.ini'))

logging.getLogger('boto').setLevel(logging.WARNING)
logging.getLogger('newrelic').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

@agent.wsgi_application()
def application(req_environ, start_response):
    """Wrapper around actual application to load config based on environment."""
    if (
            'EISITIRIO_CONFIG' not in req_environ or
            not APP.config.from_pyfile(req_environ['EISITIRIO_CONFIG'])
    ):
        start_response(b'500 Internal Server Error',
                       [(b'Content-Type', b'text/plain')])

        return [b'Bad Server Configuration']

    return APP(req_environ, start_response)

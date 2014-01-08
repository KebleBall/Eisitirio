# coding: utf-8
import site, os, sys
site.addsitedir(os.path.realpath(__file__).replace('/kebleball/','/lib/python2.7/site-packages/').replace('/wsgi.py',''))
sys.path.append(os.path.realpath(__file__).replace('/wsgi.py',''))

from kebleball import app
from werkzeug.debug import DebuggedApplication

def application(req_environ, start_response):
    if 'KEBLE_BALL_ENV' in req_environ:
        if req_environ['KEBLE_BALL_ENV'] == 'STAGING':
            app.config.from_pyfile('config/production.py')
            _app = DebuggedApplication(app, True)
            return _app(req_environ, start_response)
        elif req_environ['KEBLE_BALL_ENV'] == 'PRODUCTION':
            app.config.from_pyfile('config/production.py')
            return app(req_environ, start_response)
    else:
        return app(req_environ, start_response)
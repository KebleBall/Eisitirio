# coding: utf-8
import site, os, sys
site.addsitedir('/var/www/flask/lib/python2.7/site-packages/')
sys.path.append(os.path.realpath(__file__).replace('/wsgi.py',''))

from kebleball import app
import newrelic.agent

newrelic.agent.initialize('/var/www/flask/newrelic.ini')

@newrelic.agent.wsgi_application()
def application(req_environ, start_response):
    if 'KEBLE_BALL_ENV' in req_environ:
        if req_environ['KEBLE_BALL_ENV'] == 'STAGING':
            app.config.from_pyfile('config/staging.py')
            return app(req_environ, start_response)
        elif req_environ['KEBLE_BALL_ENV'] == 'PRODUCTION':
            app.config.from_pyfile('config/production.py')
            return app(req_environ, start_response)
    else:
        return app(req_environ, start_response)

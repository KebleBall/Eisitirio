import site, os, sys
site.addsitedir(os.path.realpath(__file__).replace('/kebleball/','/lib/python2.7/site-packages/').replace('/wsgi.py',''))
sys.path.append(os.path.realpath(__file__).replace('/wsgi.py',''))

from kebleball import app
from werkzeug.debug import DebuggedApplication

def application(req_environ, start_response):
    os.environ['KEBLE_BALL_ENV'] = req_environ['KEBLE_BALL_ENV']
    _app = DebuggedApplication(app, True)
    return _app(req_environ, start_response)
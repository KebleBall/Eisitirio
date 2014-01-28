#! /usr/bin/env python2
# coding: utf-8

from kebleball import app
from werkzeug.contrib.profiler import ProfilerMiddleware

app.config['PROFILE'] = True
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions = [30])

if __name__ == '__main__':
    app.run()

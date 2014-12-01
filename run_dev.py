#! /usr/bin/env python2
# coding: utf-8

from kebleball import app

from werkzeug.contrib.profiler import ProfilerMiddleware

f = open('/tmp/kebleball.profiler.log', 'w')

if __name__ == '__main__':
    app.config.from_pyfile('config/development.py')
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, f, ('cumtime','time','calls'))
    app.run()

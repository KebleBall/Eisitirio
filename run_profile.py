#! /usr/bin/env python2
# coding: utf-8
"""Executable to run the Keble Ball Ticketing System with profiling."""

from __future__ import unicode_literals

from werkzeug.contrib import profiler

from kebleball import app
from kebleball import system # pylint: disable=unused-import

APP = app.APP

APP.config.from_pyfile('config/development.py')
APP.config['PROFILE'] = True
APP.wsgi_app = profiler.ProfilerMiddleware(APP.wsgi_app, restrictions=[30])

if __name__ == '__main__':
    APP.run()

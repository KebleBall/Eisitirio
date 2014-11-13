#! /usr/bin/env python2
# coding: utf-8
"""Executable to run the Keble Ball Ticketing System with profiling."""

from werkzeug.contrib.profiler import ProfilerMiddleware

import kebleball

APP = kebleball.APP

APP.config['PROFILE'] = True
APP.wsgi_app = ProfilerMiddleware(APP.wsgi_app, restrictions=[30])

if __name__ == '__main__':
    APP.run()

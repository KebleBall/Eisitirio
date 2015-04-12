#! /usr/bin/env python2
# coding: utf-8
"""Executable to run the Keble Ball Ticketing System in staging mode."""

from __future__ import unicode_literals

from kebleball import app

if __name__ == '__main__':
    app.APP.config.from_pyfile('config/staging.py')
    app.APP.run()

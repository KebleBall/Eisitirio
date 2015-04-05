#! /usr/bin/env python2
# coding: utf-8
"""Executable to run the Keble Ball Ticketing System in production mode."""

from __future__ import unicode_literals

import kebleball

APP = kebleball.APP

if __name__ == '__main__':
    APP.config.from_pyfile('config/production.py')
    APP.run()

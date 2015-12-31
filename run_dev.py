#! /usr/bin/env python2
# coding: utf-8
"""Executable to run Eisitirio in development mode."""

from __future__ import unicode_literals

from eisitirio import app
from eisitirio import system # pylint: disable=unused-import

if __name__ == '__main__':
    app.APP.config.from_pyfile('config/development.py')
    app.APP.run()

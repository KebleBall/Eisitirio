#! /usr/bin/env python2
# coding: utf-8

from kebleball import app

if __name__ == '__main__':
    app.config.from_pyfile('config/development.py')
    app.run()

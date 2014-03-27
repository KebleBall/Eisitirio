#! /usr/bin/env python2
# coding: utf-8

import os
from kebleball import app

if __name__ == '__main__':
    app.config.from_pyfile('config/staging.py')
    app.run()

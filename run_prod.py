#! /usr/bin/env python2
# coding: utf-8

import os
from kebleball import app

if __name__ == '__main__':
    os.environ['KEBLE_BALL_ENV'] = 'PRODUCTION'
    app.run()

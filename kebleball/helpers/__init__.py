# coding: utf-8
from datetime import datetime
import random
import string

from kebleball import app

APP = app.APP

def generate_key(length, choices=None):
    if choices is None:
        choices = (
            string.ascii_lowercase +
            string.ascii_uppercase +
            string.digits
        )

    return ''.join(random.choice(choices) for x in xrange(length))

def get_boolean_config(key):
    if isinstance(APP.config[key], datetime):
        return datetime.utcnow() >= APP.config[key]
    else:
        return APP.config[key]

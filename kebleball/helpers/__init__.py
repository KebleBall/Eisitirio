# coding: utf-8
from datetime import datetime
import random
import string

from kebleball.app import app

def generate_key(length, choices=None):
    if choices is None:
        choices = (
            string.ascii_lowercase +
            string.ascii_uppercase +
            string.digits
        )

    return ''.join(random.choice(choices) for x in xrange(length))

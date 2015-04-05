# coding: utf-8
"""Module containing helper functions and classes."""

import random
import string

def generate_key(length, choices=None):
    """Generate a randomised key of a given length.

    Random keys are used for verifying the authenticity of email confirmations,
    password resets and resale actions.

    Args:
        length: (int) Length (in characters) of the returned string
        choices: (list or None) List of characters to use in the key. If not
            given, defaults to alphanumerics

    Returns:
        (str) a randomly generated string
    """
    if choices is None:
        choices = (
            string.ascii_lowercase +
            string.ascii_uppercase +
            string.digits
        )

    return ''.join(random.choice(choices) for x in xrange(length))


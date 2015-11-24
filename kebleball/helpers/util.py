# coding: utf-8
"""Module containing helper functions."""

import random
import string

def generate_key(length, choices=None):
    """Generate a randomised key of a given length.

    Random keys are used for verifying the authenticity of email confirmations
    and password resets.

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


def parse_pounds_pence(form, pounds_key, pence_key):
    """Parse price form fields into its value in pence.

    Args:
        form: (dict) The form object containing the submitted values.
        pounds_key: (str) The name of the form field for pounds.
        pence_key: (str) The name of the form field for pence.

    Returns:
        (int) The parsed price value.
    """
    try:
        amount = int(form[pounds_key]) * 100
    except ValueError:
        # Assume pounds is none if left blank
        amount = 0

    try:
        return amount + int(form[pence_key])
    except ValueError:
        # Assume pence is none if left blank
        return amount

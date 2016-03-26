# coding: utf-8
"""Module containing helper functions."""

from __future__ import unicode_literals

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


def format_timedelta(td):
    """Format a timedelta into a human readable format."""
    weeks, days = divmod(td.days, 7)

    minutes, seconds = divmod(td.seconds, 60)

    hours, minutes = divmod(minutes, 60)

    components = []

    if weeks:
        components.append(
            "{0} week{1}".format(
                weeks,
                "s" if weeks > 1 else ""
            )
        )

    if days:
        components.append(
            "{0} day{1}".format(
                days,
                "s" if days > 1 else ""
            )
        )

    if hours:
        components.append(
            "{0} hour{1}".format(
                hours,
                "s" if hours > 1 else ""
            )
        )

    if minutes:
        components.append(
            "{0} minute{1}".format(
                minutes,
                "s" if minutes > 1 else ""
            )
        )

    if seconds:
        components.append(
            "{0} second{1}".format(
                seconds,
                "s" if seconds > 1 else ""
            )
        )

    if td.microseconds:
        components.append(
            "{0} microsecond{1}".format(
                td.microseconds,
                "s" if td.microseconds > 1 else ""
            )
        )

    if not components:
        return "no time at all"
    elif len(components) == 1:
        return components[0]
    else:
        return "{0} and {1}".format(
            components[0],
            components[1]
        )

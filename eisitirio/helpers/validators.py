# coding: utf-8
"""Helper functions used to validate user input."""

from __future__ import unicode_literals

import datetime

from eisitirio.database import models

def validate_voucher(code):
    """Validate a discount voucher.

    Check that the voucher exists, and that it can still be used.

    Args:
        code: (str) the voucher code identifying the discount voucher.

    Returns:
        (bool, dict(class:str, message:str), Voucher or None) returns whether
        the voucher is valid, a dict containing components of a message to be
        flashed, and if valid the voucher itself or otherwise None.
    """
    voucher = models.Voucher.query.filter(models.Voucher.code == code).first()

    if not voucher:
        result = (
            False,
            {
                'class': 'error',
                'message': ('That voucher code wasn\'t recognised. '
                            'Please ensure you have entered it correctly.')
            },
            None
        )
    else:
        if voucher.single_use and voucher.used:
            result = (
                False,
                {
                    'class': 'error',
                    'message': 'That voucher code has already been used.'
                },
                None
            )
        elif (voucher.expires is not None
              and voucher.expires < datetime.datetime.utcnow()):
            result = (
                False,
                {
                    'class': 'error',
                    'message': 'That voucher code has expired.'
                },
                None
            )
        else:
            if voucher.discount_type == 'Fixed Price':
                message = (
                    'This voucher gives a fixed price of &pound;{0:.2f} for '
                ).format(
                    (voucher.discount_value / 100.0)
                )
            elif voucher.discount_type == 'Fixed Discount':
                message = (
                    'This voucher gives a fixed &pound;{0:.2f} discount off '
                ).format(
                    (voucher.discount_value / 100.0)
                )
            else:
                message = 'This voucher gives a {0:d}% discount off '.format(
                    voucher.discount_value
                )

            if voucher.applies_to == 'Ticket':
                message = message + 'one ticket.'
            else:
                message = message + 'all tickets purchased in one transaction.'

            result = (
                True,
                {
                    'class': 'success',
                    'message': message
                },
                voucher
            )

    return result

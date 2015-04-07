# coding: utf-8
"""Helper functions used to validate user input."""

from __future__ import unicode_literals

import datetime

from kebleball.database import models

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

def validate_referrer(email, current_user):
    """Validate a referrer.

    Check that the user referred to exists, and that it is not the current user.

    Args:
        email: (str) the email address entered as referrer.
        current_user: (models.User) the currently logged in user who has been
            referred

    Returns:
        (bool, dict(class:str, message:str), User or None) returns whether
        the referrer is a valid user, a dict containing components of a message
        to be flashed, and if valid the user itself or otherwise None.
    """
    user = models.User.get_by_email(email)

    if user:
        if user == current_user:
            result = (
                False,
                {
                    'class': 'error',
                    'message': 'You can\'t credit yourself for your own order!'
                },
                None
            )
        else:
            result = (
                True,
                {
                    'class': 'success',
                    'message': '{0} will be credited for your order.'.format(
                        user.forenames
                    )
                },
                user
            )
    else:
        result = (
            False,
            {
                'class': 'warning',
                'message': (
                    'No user with that email address was found, have you '
                    'entered it correctly? The person who referred you must '
                    'have an account before they can be given credit for your '
                    'order.'
                )
            },
            None
        )

    return result

def validate_resale_email(email, current_user):
    """Validate a user to resell tickets to.

    Check that the user referred to exists, and that it is not the current user.

    Args:
        email: (str) the email address entered as recipient.
        current_user: (models.User) the currently logged in user who is
            reselling tickets

    Returns:
        (bool, dict(class:str, message:str), User or None) returns whether
        the email is associated with a valid user, a dict containing components
        of a message to be flashed, and if valid the user itself or otherwise
        None.
    """
    user = models.User.get_by_email(email)

    if user:
        if user == current_user:
            result = (
                False,
                {
                    'class': 'info',
                    'message': (
                        'There is very little, if any, point in reselling '
                        'tickets to yourself...'
                    )
                },
                None
            )
        else:
            result = (
                True,
                {
                    'class': 'success',
                    'message': (
                        '{0} will receive an email to confirm the resale.'
                    ).format(user.forenames)
                },
                None
            )
    else:
        result = (
            False,
            {
                'class': 'warning',
                'message': (
                    'No user with that email address was found, have you '
                    'entered it correctly? The person who you are reselling '
                    'to must have an account before they can buy tickets from '
                    'you.'
                )
            },
            None
        )

    return result

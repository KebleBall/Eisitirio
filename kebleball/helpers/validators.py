# coding: utf-8

from datetime import datetime

from kebleball.database import voucher
from kebleball.database import user

Voucher = voucher.Voucher
User = user.User

def validateVoucher(code):
    voucher = Voucher.query.filter(Voucher.code==code).first()

    if not voucher:
        result = (
            False,
            {
                'class': 'error',
                'message': ("That voucher code wasn't recognised. "
                            "Please ensure you have entered it correctly.")
            },
            None
        )
    else:
        if voucher.single_use and voucher.used:
            result = (
                False,
                {
                    'class': 'error',
                    'message': "That voucher code has already been used."
                },
                None
            )
        elif (voucher.expires is not None
              and voucher.expires < datetime.utcnow()):
            result = (
                False,
                {
                    'class': 'error',
                    'message': "That voucher code has expired."
                },
                None
            )
        else:
            if voucher.discount_type == 'Fixed Price':
                message = "This voucher gives a fixed price of &pound;{0:.2f} for ".format(
                    (voucher.discount_value / 100.0)
                )
            elif voucher.discount_type == 'Fixed Discount':
                message = "This voucher gives a fixed &pound;{0:.2f} discount off ".format(
                    (voucher.discount_value / 100.0)
                )
            else:
                message = "This voucher gives a {0:d}% discount off ".format(
                    voucher.discount_value
                )

            if voucher.applies_to == "Ticket":
                message = message + "one ticket."
            else:
                message = message + "all tickets purchased in one transaction."

            result = (
                True,
                {
                    'class': 'success',
                    'message': message
                },
                voucher
            )

    return result

def validateReferrer(email, current_user):
    user = User.get_by_email(email)

    if user:
        if user == current_user:
            result = (
                False,
                {
                    'class': 'error',
                    'message': "You can't credit yourself for your own order!"
                },
                None
            )
        else:
            result = (
                True,
                {
                    'class': 'success',
                    'message': '{0} will be credited for your order.'.format(user.forenames)
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
                    'entered it correctly? '
                    'The person who referred you must have '
                    'an account before they can be given credit for your order.'
                )
            },
            None
        )

    return result

def validateResaleEmail(email, current_user):
    user = User.get_by_email(email)

    if user:
        if user == current_user:
            result = (
                False,
                {
                    'class': 'info',
                    'message': "There is very little, if any, point in reselling tickets to yourself..."
                },
                None
            )
        else:
            result = (
                True,
                {
                    'class': 'success',
                    'message': '{0} will receive an email to confirm the resale.'.format(user.forenames)
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

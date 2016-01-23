# coding: utf-8
"""Permissions/possessions for users."""

from eisitirio import app
from eisitirio.database import models

@models.User.possession()
def tickets(user):
    """Does the user have any tickets?"""
    return len([x for x in user.tickets
                if not x.cancelled]) > 0

@models.User.possession()
def uncollected_tickets(user):
    """Does the user have any uncollected tickets?"""
    return len([x for x in user.tickets
                if not x.cancelled and not x.collected]) > 0

@models.User.possession()
def collected_tickets(user):
    """Has the user collected any tickets?"""
    return len([x for x in user.tickets
                if not x.cancelled and x.collected]) > 0

@models.User.possession()
def unpaid_tickets(user, method=None):
    """Does the user have any unpaid tickets?

    Checks if the user has tickets which they haven't yet paid for,
    potentially filtered by payment method.

    Args:
        method: (str) payment method to search for unpaid tickets by

    Returns:
        (bool) whether there are any tickets owned by the user (and with
        the given payment method set if given) which have not been paid for
    """
    if method is None:
        return len(
            [
                x for x in user.tickets if (
                    not x.paid and
                    not x.cancelled
                )
            ]
        ) > 0
    else:
        return len(
            [
                x for x in user.tickets if (
                    x.payment_method == method and
                    not x.paid and
                    not x.cancelled
                )
            ]
        ) > 0

@models.User.possession()
def paid_tickets(user, method=None):
    """Does the user have any unpaid tickets?

    Checks if the user has tickets which they have paid for, potentially
    filtered by payment method.

    Args:
        method: (str) payment method to search for paid tickets by

    Returns:
        (bool) whether there are any tickets owned by the user (and with
        the given payment method set if given) which have been paid for
    """
    if method is None:
        return len(
            [
                x for x in user.tickets if (
                    x.paid and
                    not x.cancelled
                )
            ]
        ) > 0
    else:
        return len(
            [
                x for x in user.tickets if (
                    x.payment_method == method and
                    x.paid and
                    not x.cancelled
                )
            ]
        ) > 0

@models.User.permission()
def pay_by_battels(user):
    """Is the user able to pay by battels?

    The requirement for this is that the user is a current member of the
    relevant college(s), and that it is either Michaelmas or Hilary term.
    The logic determining whether the user is a current member is carried
    out at registration (and based on whether their email matches one in our
    list of battelable emails). Alternately, this can be forced by an admin
    through the admin interface if the user is not automatically recognised.
    Given this, it suffices to only check if the user has a defined battels
    account on the system.
    """
    return (
        user.battels is not None and
        app.APP.config['CURRENT_TERM'] != 'TT'
    )

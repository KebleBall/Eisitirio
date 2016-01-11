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

@models.User.permission()
def wait(self):
    """Can the user join the waiting list?

    Performs the necessary logic to determine if the user is permitted to
    join the waiting list for tickets

    Returns:
        (bool, int, str/None) triple of whether the user can join the
        waiting list, how many tickets the user can wait for, and an error
        message if the user cannot join the waiting list.
    """
    if not app.APP.config['WAITING_OPEN']:
        return (
            False,
            0,
            'the waiting list is currently closed.'
        )

    tickets_owned = self.tickets.filter(
        models.Ticket.cancelled == False # pylint: disable=singleton-comparison
    ).count()

    if tickets_owned >= app.APP.config['MAX_TICKETS']:
        return (
            False,
            0,
            (
                'you have too many tickets. Please contact<a href="{0}"> '
                'the ticketing officer</a> if you wish to purchase more '
                'than {1} tickets.'
            ).format(
                app.APP.config['TICKETS_EMAIL_LINK'],
                app.APP.config['MAX_TICKETS']
            )
        )

    waiting_for = self.waiting_for()
    if waiting_for >= app.APP.config['MAX_TICKETS_WAITING']:
        return (
            False,
            0,
            (
                'you are already waiting for too many tickets. Please '
                'rejoin the waiting list once you have been allocated the '
                'tickets you are currently waiting for.'
            )
        )

    return (
        True,
        min(
            app.APP.config['MAX_TICKETS_WAITING'] - waiting_for,
            app.APP.config['MAX_TICKETS'] - tickets_owned
        ),
        None
    )

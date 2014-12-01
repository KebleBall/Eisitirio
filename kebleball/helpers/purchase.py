# coding: utf-8

from kebleball.app import app
from kebleball.database.ticket import Ticket
from kebleball.database.user import User
from kebleball.database.waiting import Waiting
from kebleball.helpers import get_boolean_config

def canBuy(user):
    if get_boolean_config('LIMITED_RELEASE'):
        if not (
                user.college.name == "Keble" and
                user.affiliation.name in [
                    "Student",
                    "Graduand",
                    "Staff/Fellow",
                    "Foreign Exchange Student",
                ]
        ):
            return (
                False,
                0,
                (
                    "tickets are on limited release to current Keble members and "
                    "Keble graduands only."
                )
            )
        elif not user.affiliation_verified:
            return (
                False,
                0,
                (
                    "your affiliation has not been verified yet. You will be "
                    "informed by email when you are able to purchase tickets."
                )
            )
    elif not get_boolean_config('TICKETS_ON_SALE'):
        return (
            False,
            0,
            (
                'tickets are currently not on sale. Tickets may become available '
                'for purchase or through the waiting list, please check back at a '
                'later date.'
            )
        )

    # Don't allow people to buy tickets unless waiting list is empty
    if Waiting.query.count() > 0:
        return (
            False,
            0,
            'there are currently people waiting for tickets.'
        )

    unpaidTickets = user.tickets \
        .filter(Ticket.cancelled==False) \
        .filter(Ticket.paid==False) \
        .count()
    if unpaidTickets >= app.config['MAX_UNPAID_TICKETS']:
        return (
            False,
            0,
            (
                'you have too many unpaid tickets. Please pay '
                'for your tickets before reserving any more.'
            )
        )

    ticketsOwned = user.tickets \
        .filter(Ticket.cancelled==False) \
        .count()
    if (
            get_boolean_config('TICKETS_ON_SALE') and
            ticketsOwned >= app.config['MAX_TICKETS']
    ):
        return (
            False,
            0,
            (
                'you already own too many tickets. Please contact <a href="{0}">the '
                'ticketing officer</a> if you wish to purchase more than {1} '
                'tickets.'
            ).format(
                app.config['TICKETS_EMAIL_LINK'],
                app.config['MAX_TICKETS']
            )
        )
    elif (
            get_boolean_config('LIMITED_RELEASE') and
            ticketsOwned >= app.config['LIMITED_RELEASE_MAX_TICKETS']
    ):
        return (
            False,
            0,
            (
                'you already own {0} tickets. During pre-release, only {0} '
                'tickets may be bought per person.'
            ).format(
                app.config['LIMITED_RELEASE_MAX_TICKETS']
            )
        )


    ticketsAvailable = app.config['TICKETS_AVAILABLE'] - Ticket.count()
    if ticketsAvailable <= 0:
        return (
            False,
            0,
            (
                'there are no tickets currently available. Tickets may become '
                'available for purchase or through the waiting list, please '
                'check back at a later date.'
            )
        )

    if get_boolean_config('TICKETS_ON_SALE'):
        max_tickets = app.config['MAX_TICKETS']
    elif get_boolean_config('LIMITED_RELEASE'):
        max_tickets = app.config['LIMITED_RELEASE_MAX_TICKETS']

    return (
        True,
        min(
            ticketsAvailable,
            app.config['MAX_TICKETS_PER_TRANSACTION'],
            max_tickets - ticketsOwned,
            app.config['MAX_UNPAID_TICKETS'] - unpaidTickets
        ),
        None
    )

def canWait(user):
    waitingOpen = get_boolean_config('WAITING_OPEN')

    if not waitingOpen:
        return (
            False,
            0,
            'the waiting list is currently closed.'
        )

    ticketsOwned = user.tickets \
        .filter(Ticket.cancelled==False) \
        .count()
    if ticketsOwned >= app.config['MAX_TICKETS']:
        return (
            False,
            0,
            (
                'you have too many tickets. Please contact <a href="{0}">the '
                'ticketing officer</a> if you wish to purchase more than {1} '
                'tickets.'
            ).format(
                app.config['TICKETS_EMAIL_LINK'],
                app.config['MAX_TICKETS']
            )
        )

    waitingFor = user.waitingFor()
    if waitingFor >= app.config['MAX_TICKETS_WAITING']:
        return (
            False,
            0,
            (
                'you are already waiting for too many tickets. Please rejoin '
                'the waiting list once you have been allocated the tickets '
                'you are currently waiting for.'
            )
        )

    return (
        True,
        min(
            app.config['MAX_TICKETS_WAITING'] - waitingFor,
            app.config['MAX_TICKETS'] - ticketsOwned
        ),
        None
    )

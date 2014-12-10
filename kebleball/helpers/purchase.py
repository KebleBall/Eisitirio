# coding: utf-8
from kebleball.app import app
from kebleball.database.ticket import Ticket
from kebleball.database.user import User
from kebleball.database.waiting import Waiting
from datetime import datetime

def canBuy(user):
    if isinstance(app.config['TICKETS_ON_SALE'], datetime):
        if app.config['TICKETS_ON_SALE'] > datetime.utcnow():
            on_sale = False
        else:
            on_sale = True
    else:
        on_sale = app.config['TICKETS_ON_SALE']

    if not on_sale:
        (waitingAllowed, waitFor, message) = canWait(user)
        return (
            False,
            0,
            waitingAllowed,
            (
                'tickets are currently not on sale. Tickets may become '
                'available for purchase or through the waiting list, please '
                'check back at a later date.'
            )
        )

    # Don't allow people to buy tickets unless waiting list is empty
    if Waiting.query.count() > 0:
        return (
            False,
            0,
            True,
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
            False,
            (
                'you have too many unpaid tickets. Please pay '
                'for your tickets before reserving any more.'
            )
        )

    ticketsOwned = user.tickets \
        .filter(Ticket.cancelled==False) \
        .count()
    if ticketsOwned >= app.config['MAX_TICKETS']:
        return (
            False,
            0,
            False,
            (
                'you have too many tickets. Please contact <a href="{0}">the '
                'ticketing officer</a> if you wish to purchase more than {1} '
                'tickets.'
            ).format(
                app.config['TICKETS_EMAIL_LINK'],
                app.config['MAX_TICKETS']
            )
        )

    ticketsAvailable = app.config['TICKETS_AVAILABLE'] - Ticket.count()
    if ticketsAvailable <= 0:
        return (
            False,
            0,
            True,
            (
                'there are no tickets currently available. Tickets may become '
                'available for purchase or through the waiting list, please '
                'check back at a later date.'
            )
        )

    return (
        True,
        min(
            ticketsAvailable,
            app.config['MAX_TICKETS_PER_TRANSACTION'],
            app.config['MAX_TICKETS'] - ticketsOwned,
            app.config['MAX_UNPAID_TICKETS'] - unpaidTickets
        ),
        False,
        None
    )

def canWait(user):
    if isinstance(app.config['WAITING_OPEN'], datetime):
        if app.config['WAITING_OPEN'] > datetime.utcnow():
            waitingOpen = False
        else:
            waitingOpen = True
    else:
        waitingOpen = app.config['WAITING_OPEN']

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

    waiting_for = user.waiting_for()
    if waiting_for >= app.config['MAX_TICKETS_WAITING']:
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
            app.config['MAX_TICKETS_WAITING'] - waiting_for,
            app.config['MAX_TICKETS'] - ticketsOwned
        ),
        None
    )

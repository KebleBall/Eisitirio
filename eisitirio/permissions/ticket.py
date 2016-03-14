# coding: utf-8
"""Permissions/possessions for tickets."""

from flask.ext import login

from eisitirio import app
from eisitirio.database import models

def _ticket_is_cancellable(ticket):
    """Check whether a ticket can be automatically cancelled and refunded."""
    if ticket.cancelled:
        return False
    elif ticket.collected:
        return False
    elif ticket.has_holder():
        return False
    elif not ticket.paid:
        return True
    elif ticket.payment_method == 'Card':
        return True
    elif ticket.payment_method == 'Battels':
        return app.APP.config['CURRENT_TERM'] != 'TT'
    elif ticket.payment_method == 'Free':
        return True
    else:
        return False


@models.Ticket.permission()
def be_cancelled(ticket):
    """Check whether a user can cancel a ticket."""
    if not _ticket_is_cancellable(ticket):
        return False
    elif login.current_user.is_admin:
        return True
    elif app.APP.config['LOCKDOWN_MODE']:
        return False
    elif not app.APP.config['ENABLE_CANCELLATION']:
        return False
    else:
        return True

@models.Ticket.permission()
def be_resold(ticket):
    """Check whether a user can resell a ticket."""
    if not _ticket_is_cancellable(ticket):
        return False
    elif login.current_user.is_admin:
        return True
    elif app.APP.config['LOCKDOWN_MODE']:
        return False
    elif not app.APP.config['ENABLE_RESALE']:
        return False
    else:
        return True

@models.Ticket.permission()
def be_collected(ticket):
    """Check whether a ticket can be collected."""
    return (
        ticket.paid and
        not ticket.collected and
        not ticket.cancelled and
        ticket.has_holder() and
        ticket.holder.photo.verified
    )

@models.Ticket.permission()
def buy_postage(ticket):
    """Check whether postage can be bought for this ticket."""
    return (
        ticket.paid and
        not ticket.cancelled and
        not ticket.collected and
        (
            ticket.postage is None or
            not ticket.postage.paid
        ) and
        not app.APP.config['LOCKDOWN_MODE'] and
        app.APP.config['ENABLE_SEPARATE_POSTAGE']
    )

@models.Ticket.permission()
def be_paid_for(ticket):
    """Check whether this ticket can be paid for."""
    return not ticket.paid and not ticket.cancelled

@models.Ticket.permission()
def be_reclaimed(ticket):
    """Can the user reclaim/relinquish a ticket."""
    return ticket.has_holder() and (
        login.current_user.is_admin or (
            not app.APP.config['LOCKDOWN_MODE'] and
            app.APP.config['ENABLE_RECLAIMING_TICKETS']
        )
    )

@models.Ticket.possession()
def holder(ticket):
    """Is this ticket held by a user."""
    return ticket.holder is not None

@models.Ticket.permission()
def be_claimed(ticket):
    """Can this ticket be claimed."""
    return not ticket.has_holder() and (
        login.current_user.is_admin or
        ticket.claims_made < app.APP.config['MAX_TICKET_CLAIMS']
    )

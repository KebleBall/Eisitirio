# coding: utf-8
"""Permissions/possessions for tickets."""

from eisitirio import app
from eisitirio.database import models

@models.Ticket.permission()
def be_cancelled(ticket):
    """Check whether a ticket can be (automatically) cancelled."""
    if ticket.cancelled:
        return False
    elif app.APP.config['LOCKDOWN_MODE']:
        return False
    elif ticket.collected:
        return False
    elif ticket.holder is not None:
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
def be_resold(ticket):
    return app.APP.config['ENABLE_RESALE'] and be_cancelled(ticket)

@models.Ticket.permission()
def be_collected(ticket):
    """Check whether a ticket can be collected."""
    # TODO
    return (
        ticket.paid and
        not ticket.collected and
        not ticket.cancelled and
        ticket.name is not None
    )

@models.Ticket.permission()
def change_name(ticket):
    """Check whether a ticket's name can be changed."""
    # TODO
    return not (
        app.APP.config['LOCKDOWN_MODE'] or
        ticket.cancelled or
        ticket.collected
    )

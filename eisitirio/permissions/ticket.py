# coding: utf-8
"""Permissions/possessions for tickets."""

from eisitirio import app
from eisitirio.database import models

@models.Ticket.permission()
def be_cancelled(ticket):
    """Check whether a ticket can be (automatically) cancelled."""
    # TODO
    return False

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

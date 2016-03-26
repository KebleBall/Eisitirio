# coding: utf-8
"""Logic regarding collection of tickets."""

from __future__ import unicode_literals

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

APP = app.APP
DB = db.DB

# Make sure barcode can't be empty
# Make sure ticket can't be collected twice


def collect_ticket(ticket, barcode):
    """Mark a ticket as collected, and set its barcode.

    Checks that the barcode has not been used already, and that the ticket has
    not already been collected.

    Returns:
        (str or None) an error message if the collection failed, else None.
    """
    if ticket.collected:
        return 'Ticket has already been collected.'

    if not barcode:
        return 'Barcode must not be empty.'

    if models.Ticket.query.filter(
            models.Ticket.barcode == barcode
    ).count():
        return 'Barcode has already been used for a ticket.'

    ticket.barcode = barcode
    ticket.collected = True
    DB.session.commit()

    APP.log_manager.log_event(
        'Collected',
        tickets=[ticket]
    )

    return None

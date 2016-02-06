# coding: utf-8
"""Helper functions for computing statistics."""

from __future__ import unicode_literals

import collections

import sqlalchemy

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

APP = app.APP
DB = db.DB

# pylint: disable=singleton-comparison

def get_revenue():
    """Get statistics about revenue."""

    return collections.OrderedDict([
        (
            'Total value of all tickets',
            _maybe_int(
                DB.session.query(
                    sqlalchemy.func.sum(models.Ticket.price_)
                ).scalar()
            )
        ),
        (
            'Total value of active tickets',
            _maybe_int(
                DB.session.query(
                    sqlalchemy.func.sum(models.Ticket.price_)
                ).filter(
                    models.Ticket.cancelled == False
                ).scalar()
            )
        ),
        (
            'Total value of cancelled tickets',
            _maybe_int(
                DB.session.query(
                    sqlalchemy.func.sum(models.Ticket.price_)
                ).filter(
                    models.Ticket.cancelled == True
                ).scalar()
            )
        ),
        (
            'Total value of paid tickets',
            _maybe_int(
                DB.session.query(
                    sqlalchemy.func.sum(models.Ticket.price_)
                ).filter(
                    models.Ticket.paid == True
                ).filter(
                    models.Ticket.cancelled == False
                ).scalar()
            )
        ),
        (
            'Total eWay charges (payments minus refunds)',
            _maybe_int(
                DB.session.query(
                    sqlalchemy.func.sum(models.EwayTransaction.charged)
                ).filter(
                    models.EwayTransaction.completed != None
                ).scalar()
            ) - _maybe_int(
                DB.session.query(
                    sqlalchemy.func.sum(models.EwayTransaction.refunded)
                ).filter(
                    models.EwayTransaction.completed != None
                ).scalar()
            )
        ),
        (
            'Total Michaelmas battels charges',
            _maybe_int(
                DB.session.query(
                    sqlalchemy.func.sum(models.Battels.michaelmas_charge)
                ).scalar()
            )
        ),
        (
            'Total Hilary battels charges',
            _maybe_int(
                DB.session.query(
                    sqlalchemy.func.sum(models.Battels.hilary_charge)
                ).scalar()
            )
        ),
        (
            'Total postage value',
            _maybe_int(
                DB.session.query(
                    sqlalchemy.func.sum(models.Postage.price)
                ).filter(
                    models.Postage.paid == True
                ).filter(
                    models.Postage.cancelled == False
                ).scalar()
            )
        ),
    ])

def get(group):
    """Hacky wrapper around each of the _get_<group_name> functions."""
    return globals()['_get_{0}'.format(group)]()

def _get_college_users():
    """Get the number of registered users from each college."""
    return collections.OrderedDict([
        (
            college.name,
            models.User.query.filter(
                models.User.college_id == college.object_id
            ).count()
        )
        for college in models.College.query.all()
    ])

def _get_payment_methods():
    """Get the number of tickets paid for with each payment method."""
    return collections.OrderedDict([
        (
            name,
            models.Ticket.query.join(
                models.TicketTransactionItem.query.join(
                    models.Transaction.query.filter(
                        models.Transaction.payment_method == payment_method
                    ).filter(
                        models.Transaction.paid == True
                    ).subquery(),
                    models.TicketTransactionItem.transaction
                ).subquery(reduce_columns=True),
                models.Ticket.transaction_items
            ).count()
        )
        for name, payment_method in collections.OrderedDict([
            ('Battels', 'Battels'),
            ('Card', 'Card'),
            ('Free', 'Free'),
            ('Unknown', 'Dummy'),
        ]).iteritems()
    ])

def _get_ticket_types():
    """Get the number of active tickets by type."""
    return collections.OrderedDict([
        (
            ticket_type.name,
            models.Ticket.query.filter(
                models.Ticket.ticket_type == ticket_type.slug
            ).filter(
                models.Ticket.cancelled == False
            ).count()
        )
        for ticket_type in APP.config['TICKET_TYPES']
    ])

def _get_total_ticket_sales():
    """Get the total number of tickets in various states."""
    return _get_ticket_sales(models.Ticket.query)

def _get_guest_ticket_sales():
    """Get the total number of guest tickets in various states."""
    statistics = collections.OrderedDict([
        ('Available', APP.config['GUEST_TICKETS_AVAILABLE']),
    ])

    statistics.update(
        _get_ticket_sales(
            models.Ticket.query.filter(
                models.Ticket.ticket_type.in_(
                    APP.config['GUEST_TYPE_SLUGS']
                )
            )
        )
    )

    return statistics

def _get_ticket_sales(query):
    """Get numbers of tickets in various states, based on a filtered query."""
    return collections.OrderedDict([
        (
            'Ordered',
            query.count(),
        ),
        (
            'Cancelled',
            query.filter(
                models.Ticket.cancelled == True
            ).count(),
        ),
        (
            'Unpaid',
            query.filter(
                models.Ticket.cancelled == False
            ).filter(
                models.Ticket.paid == False
            ).count(),
        ),
        (
            'Paid',
            query.filter(
                models.Ticket.cancelled == False
            ).filter(
                models.Ticket.paid == True
            ).filter(
                models.Ticket.collected == False
            ).count(),
        ),
        (
            'Collected',
            query.filter(
                models.Ticket.cancelled == False
            ).filter(
                models.Ticket.paid == True
            ).filter(
                models.Ticket.collected == True
            ).filter(
                models.Ticket.entered == False
            ).count(),
        ),
        (
            'Entered',
            query.filter(
                models.Ticket.cancelled == False
            ).filter(
                models.Ticket.paid == True
            ).filter(
                models.Ticket.collected == True
            ).filter(
                models.Ticket.entered == True
            ).count(),
        ),
    ])

def _get_waiting():
    return collections.OrderedDict([
        (
            'Users Waiting',
            models.User.query.join(
                models.Waiting.query.subquery(),
                models.User.waiting
            ).count(),
        ),
        (
            'Tickets Waiting',
            _maybe_int(
                DB.session.query(
                    sqlalchemy.func.sum(
                        models.Waiting.waiting_for
                    )
                ).scalar()
            ),
        )
    ])

def _maybe_int(value):
    """Convert the result of an sqlalchemy scalar to an int."""
    if value is None:
        return 0
    else:
        return int(value)

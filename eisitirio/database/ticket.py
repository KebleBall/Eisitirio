# coding: utf-8
"""Database model for tickets."""

from __future__ import unicode_literals

import datetime

from eisitirio import app
from eisitirio.database import db

APP = app.APP
DB = db.DB

class Ticket(DB.Model):
    """Model for tickets."""
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    ticket_type = DB.Column(
        DB.Unicode(50),
        nullable=False
    )

    paid = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )
    collected = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )
    entered = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )
    cancelled = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )

    price_ = DB.Column(
        DB.Integer(),
        nullable=False
    )
    name = DB.Column(
        DB.Unicode(120),
        nullable=True
    )
    note = DB.Column(
        DB.UnicodeText(),
        nullable=True
    )
    expires = DB.Column(
        DB.DateTime(),
        nullable=True
    )
    barcode = DB.Column(
        DB.Unicode(20),
        unique=True,
        nullable=True
    )

    owner_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=False
    )
    owner = DB.relationship(
        'User',
        backref=DB.backref(
            'tickets',
            lazy='dynamic',
            order_by=b'Ticket.cancelled'
        ),
        foreign_keys=[owner_id]
    )

    def __init__(self, owner, ticket_type, price):
        self.owner = owner
        self.ticket_type = ticket_type
        self.price = price

        self.expires = (datetime.datetime.utcnow() +
                        APP.config['TICKET_EXPIRY_TIME'])

    def __repr__(self):
        return '<Ticket {0} owned by {1} ({2})>'.format(
            self.object_id,
            self.owner.full_name,
            self.owner.object_id
        )

    @property
    def price_pounds(self):
        """Get the price of this ticket as a string of pounds and pence."""
        price = '{0:03d}'.format(self.price)
        return price[:-2] + '.' + price[-2:]

    @property
    def description(self):
        """Get a description of the ticket with the type and guest name."""
        return '{0} Ticket ({1})'.format(
            self.ticket_type,
            self.name if self.name else 'No Name Set'
        )

    @property
    def payment_method(self):
        """Get the payment method for this ticket."""
        if self.price == 0:
            return "Free"

        for transaction_item in self.transaction_items:
            if transaction_item.transaction.paid:
                return transaction_item.transaction.payment_method

        return "Unknown Payment Method"

    @property
    def price(self):
        """Get the price of the ticket."""
        return self.price_

    @price.setter
    def price(self, value):
        """Set the price of the ticket."""
        self.price_ = max(value, 0)

        if self.price_ == 0:
            self.mark_as_paid()

    def mark_as_paid(self):
        """Mark the ticket as paid, and clear any expiry."""
        self.paid = True
        self.expires = None

    def add_note(self, note):
        """Add a note to the ticket."""
        if not note.endswith('\n'):
            note = note + '\n'

        if self.note is None:
            self.note = note
        else:
            self.note = self.note + note

    def can_be_cancelled(self):
        """Check whether a ticket can be (automatically) cancelled."""
        # TODO
        return False

    def can_be_collected(self):
        """Check whether a ticket can be collected."""
        # TODO
        return (
            self.paid and
            not self.collected and
            not self.cancelled and
            self.name is not None
        )

    def can_change_name(self):
        """Check whether a ticket's name can be changed."""
        # TODO
        return not (
            APP.config['LOCKDOWN_MODE'] or
            self.cancelled or
            self.collected
        )

    @staticmethod
    def count():
        """How many tickets have been sold."""
        # TODO
        return Ticket.query.filter(Ticket.cancelled == False).count() # pylint: disable=singleton-comparison

    @staticmethod
    def get_by_id(object_id):
        """Get a ticket object by its database ID."""
        ticket = Ticket.query.filter(Ticket.object_id == int(object_id)).first()

        if not ticket:
            return None

        return ticket

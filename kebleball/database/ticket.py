# coding: utf-8
"""Database model for tickets."""

from __future__ import unicode_literals

import datetime

from flask.ext import login
import flask

from kebleball import app
from kebleball import helpers
from kebleball.database import db

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
    barcode = DB.Column(
        DB.Unicode(20),
        unique=True,
        nullable=True
    )
    cancelled = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )

    price = DB.Column(
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

    referrer_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=True
    )
    referrer = DB.relationship(
        'User',
        backref=DB.backref(
            'referrals',
            lazy='dynamic'
        ),
        foreign_keys=[referrer_id]
    )

    def __init__(self, owner, ticket_type, price):
        self.owner = owner
        self.ticket_type = ticket_type
        self.expires = (datetime.datetime.utcnow() +
                        APP.config['TICKET_EXPIRY_TIME'])

        self.set_price(price)

    def __getattr__(self, name):
        """Magic method to generate ticket price in pounds."""
        if name == 'price_pounds':
            price = '{0:03d}'.format(self.price)
            return price[:-2] + '.' + price[-2:]
        else:
            raise AttributeError(
                'Ticket instance has no attribute "{0}"'.format(name)
            )

    def __repr__(self):
        return '<Ticket {0} owned by {1} ({2})>'.format(
            self.object_id,
            self.owner.full_name,
            self.owner_id
        )

    @property
    def description(self):
        return '{0} Ticket ({1})'.format(
            self.ticket_type,
            self.name if self.name else 'No Name Set'
        )

    def set_price(self, price):
        """Set the price of the ticket."""
        price = max(price, 0)

        self.price = price

        if price == 0:
            self.mark_as_paid()

    def mark_as_paid(self):
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
        # TODO
        return False
    def set_referrer(self, referrer):
        """Set who referred the user to buy this ticket."""
        if hasattr(referrer, 'object_id'):
            self.referrer_id = referrer.object_id
        else:
            self.referrer_id = referrer


    def can_be_collected(self):
        """Check whether a ticket can be collected."""
        return (
            self.paid and
            not self.collected and
            not self.cancelled and
            self.name is not None
        )

    def can_change_name(self):
        """Check whether a ticket's name can be changed."""
        return not (
            APP.config['LOCKDOWN_MODE'] or
            self.cancelled or
            self.collected
        )

    @staticmethod
    def count():
        """How many tickets have been sold."""
        return Ticket.query.filter(Ticket.cancelled == False).count()

    @staticmethod
    def get_by_id(object_id):
        """Get a ticket object by its database ID."""
        ticket = Ticket.query.filter(Ticket.object_id == int(object_id)).first()

        if not ticket:
            return None

        return ticket

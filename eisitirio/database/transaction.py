# coding: utf-8
"""Database model for representing a monetary exchange transaction."""

from __future__ import unicode_literals

import datetime

from flask.ext import login

from eisitirio import app
from eisitirio.database import db

DB = db.DB
APP = app.APP

class Transaction(DB.Model):
    """Model for representing a monetary exchange transaction."""
    __tablename__ = 'transaction'

    payment_method = DB.Column(
        DB.Enum(
            'Battels',
            'Card',
            'Free',
            'Dummy'
        ),
        nullable=False
    )

    paid = DB.Column(
        DB.Boolean,
        default=False,
        nullable=False
    )
    created = DB.Column(
        DB.DateTime(),
        nullable=False
    )

    user_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=False
    )
    user = DB.relationship(
        'User',
        backref=DB.backref(
            'transactions',
            lazy='dynamic'
        )
    )

    __mapper_args__ = {'polymorphic_on': payment_method}

    def __init__(self, user, payment_method):
        self.user = user
        self.payment_method = payment_method

        self.created = datetime.datetime.utcnow()

    def __repr__(self):
        return '<Transaction {0}: {1} item(s)>'.format(
            self.object_id,
            self.items.count()
        )

    @property
    def value(self):
        """Get the total value of the transaction."""
        return sum(item.value for item in self.items)

    @property
    def tickets(self):
        """Get the tickets paid for in this transaction.

        Returns a list of Ticket objects.
        """
        return list(
            item.ticket for item in self.items if item.item_type == 'Ticket'
        )

    @property
    def postage(self):
        """Get the postage paid for in this transaction.

        Returns a single Postage object, or None.
        """
        try:
            return list(
                item.postage
                for item in self.items
                if item.item_type == 'Postage'
            )[0]
        except IndexError:
            return None

    def mark_as_paid(self):
        """Mark the transaction as paid for.

        Marks all tickets in the transaction as paid for.
        """
        self.paid = True

        for ticket in self.tickets:
            ticket.mark_as_paid()

        postage = self.postage
        if postage:
            postage.paid = True

class FreeTransaction(Transaction):
    """Model for representing a transaction with no payment required.

    This class has to exist for the polymorphic typing to work.
    """
    __mapper_args__ = {'polymorphic_identity': 'Free'}

    def __init__(self, user):
        super(FreeTransaction, self).__init__(user, 'Free')

class DummyTransaction(Transaction):
    """Model for representing a dummy transaction.

    This class has to exist for the polymorphic typing to work. Dummy
    transactions are only spawned by the migration from the non-polymorphic
    style, and so this class and the corresponding identity can be removed on
    clean installs.
    """
    __mapper_args__ = {'polymorphic_identity': 'Dummy'}

    def __init__(self, user):
        super(DummyTransaction, self).__init__(user, 'Dummy')

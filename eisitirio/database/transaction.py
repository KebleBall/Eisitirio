# coding: utf-8
"""Database model for representing a monetary exchange transaction."""

from __future__ import unicode_literals

import datetime

from flask.ext import login

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import card_transaction

DB = db.DB
APP = app.APP

class Transaction(DB.Model):
    """Model for representing a monetary exchange transaction."""
    __tablename__ = 'transaction'

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

    battels_term = DB.Column(
        DB.Unicode(4),
        nullable=True
    )

    card_transaction_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('card_transaction.object_id'),
        nullable=True
    )
    card_transaction = DB.relationship(
        'CardTransaction',
        backref=DB.backref(
            'transaction',
            lazy=False,
            uselist=False
        )
    )

    def __init__(self, user):
        self.user = user
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

    @property
    def payment_method(self):
        """Get the method used for paying for this transaction."""
        if self.battels_term is not None:
            return "Battels"
        elif self.card_transaction is not None:
            return "Card"
        else:
            return "Unknown Payment Method"

    def charge_to_battels(self, term):
        """Charge this transaction to the user's battels account."""
        self.battels_term = term

        self.user.battels.charge(self.value, term)

        self.mark_as_paid()

    def charge_to_card(self):
        """Charge this transaction to a credit/debit card.

        Only creates the corresponding CardTransaction object, calling code must
        manipulate it and redirect the user to the payment gateway.
        """
        self.card_transaction = card_transaction.CardTransaction(self.user)

        return self.card_transaction

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

        APP.log_manager.log_event(
            'Completed Payment',
            self.tickets,
            login.current_user
        )

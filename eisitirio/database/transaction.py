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
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    paid = DB.Column(
        DB.Boolean,
        default=False,
        nullable=False
    )
    completed = DB.Column(
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

    address = DB.Column(
        DB.Unicode(200),
        nullable=True
    )

    def __init__(self, user, address):
        self.user = user
        self.created = datetime.datetime.utcnow()
        self.address = address

    def __repr__(self):
        return '<Transaction {0}: {1} item(s)>'.format(
            self.object_id,
            len(self.items)
        )

    @property
    def value(self):
        return sum(item.value for item in self.items)

    @property
    def tickets(self):
        return list(
            item.ticket for item in self.items if item.item_type == 'Ticket'
        )

    @property
    def payment_method(self):
        if self.battels_term is not None:
            return "Battels"
        elif self.card_transaction is not None:
            return "Card"
        else:
            return "Unknown Payment Method"

    def charge_to_battels(self, term):
        self.battels_term = term

        self.user.battels.charge(self.value, term)

        self.mark_as_paid()

    def charge_to_card(self):
        self.card_transaction = card_transaction.CardTransaction(self.user)

        return self.card_transaction

    def mark_as_paid(self):
        self.paid = True
        self.completed = True

        for ticket in self.tickets:
            ticket.mark_as_paid()

        APP.log_manager.log_event(
            'Completed Payment',
            self.tickets,
            login.current_user
        )

    @staticmethod
    def get_by_id(object_id):
        """Get a Transaction object by its database ID."""
        transaction = Transaction.query.filter(
            Transaction.object_id == int(object_id)
        ).first()

        if not transaction:
            return None

        return transaction

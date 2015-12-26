# coding: utf-8
"""Database model for representing an item in a transaction."""

from __future__ import unicode_literals

from eisitirio.database import db

DB = db.DB

class TransactionItem(DB.Model):
    """Model for representing an item in a transaction."""
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    item_type = DB.Column(
        DB.Enum(
            'Ticket',
            'Ticket Refund',
            'Administration Fee',
            'Postage'
        ),
        nullable=False
    )
    _value = DB.Column(
        DB.Integer(),
        nullable=True
    )
    _description = DB.Column(
        DB.Unicode(100),
        nullable=True
    )

    transaction_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('transaction.object_id'),
        nullable=False
    )
    transaction = DB.relationship(
        'Transaction',
        backref=DB.backref(
            'items',
            lazy='dynamic'
        )
    )

    ticket_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('ticket.object_id'),
        nullable=True
    )
    ticket = DB.relationship(
        'Ticket',
        backref=DB.backref(
            'transaction_items',
            lazy='dynamic'
        )
    )

    def __init__(self, transaction, ticket=None, item_type=None, value=None,
                 description=None):
        self.transaction = transaction

        if ticket is not None:
            self.ticket = ticket
            self.item_type = 'Ticket'
        else:
            self.item_type = item_type
            self._value = value
            self._description = description

    def __repr__(self):
        return '<TransactionItem({0})>'.format(
            self.object_id
        )

    @property
    def value(self):
        if self.ticket is not None:
            return self.ticket.price
        else:
            return self._value

    @property
    def description(self):
        if self.ticket is not None:
            return self.ticket.description
        else:
            return self._description

    @staticmethod
    def get_by_id(object_id):
        """Get a TransactionItem object by its database ID."""
        item = TransactionItem.query.filter(
            TransactionItem.object_id == int(object_id)
        ).first()

        if not item:
            return None

        return item

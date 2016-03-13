# coding: utf-8
"""Database model for representing an item in a transaction."""

from __future__ import unicode_literals

from eisitirio.database import db

DB = db.DB

class TransactionItem(DB.Model):
    """Model for representing an item in a transaction.

    Not used directly, use GenericTransactionItem, TicketTransactionItem,
    PostageTransactionItem, AdminFeeTransactionItem subtypes instead.
    """
    __tablename__ = 'transaction_item'

    item_type = DB.Column(
        DB.Enum(
            'Ticket',
            'Generic',
            'Postage',
            'AdminFee',
        ),
        nullable=False
    )

    transaction_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('transaction.object_id'),
        nullable=True
    )
    transaction = DB.relationship(
        'Transaction',
        backref=DB.backref(
            'items',
            lazy='dynamic'
        )
    )

    __mapper_args__ = {'polymorphic_on': item_type}

    def __init__(self, transaction, item_type):
        self.transaction = transaction
        self.item_type = item_type

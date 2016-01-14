# coding: utf-8
"""Database model for representing a generic item in a transaction."""

from __future__ import unicode_literals

from eisitirio.database import db
from eisitirio.database import transaction_item

DB = db.DB

class GenericTransactionItem(transaction_item.TransactionItem):
    """Model for representing a generic item in a transaction."""
    __tablename__ = 'generic_transaction_item'
    __mapper_args__ = {'polymorphic_identity': 'Generic'}

    object_id = DB.Column(
        DB.Integer(),
        DB.ForeignKey('transaction_item.object_id'),
        primary_key=True
    )

    value = DB.Column(
        DB.Integer(),
        nullable=True
    )
    description = DB.Column(
        DB.Unicode(100),
        nullable=True
    )

    def __init__(self, transaction, value, description):
        super(GenericTransactionItem, self).__init__(transaction, 'Generic')
        self.value = value
        self.description = description

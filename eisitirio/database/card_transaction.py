# coding: utf-8
"""Database model for representing a card transaction."""

from __future__ import unicode_literals

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import eway_transaction
from eisitirio.database import transaction

DB = db.DB
APP = app.APP

class CardTransaction(transaction.Transaction):
    """Model for representing a card transaction."""
    __tablename__ = 'card_transaction'
    __mapper_args__ = {'polymorphic_identity': 'Card'}

    object_id = DB.Column(
        DB.Integer(),
        DB.ForeignKey('transaction.object_id'),
        primary_key=True
    )

    eway_transaction_id = DB.Column(
        DB.Integer(),
        DB.ForeignKey('eway_transaction.object_id'),
        nullable=True
    )
    eway_transaction = DB.relationship(
        'EwayTransaction',
        backref=DB.backref(
            'transactions',
            lazy='dynamic'
        )
    )

    def __init__(self, user, eway_trans=None):
        super(CardTransaction, self).__init__(user, 'Card')

        if eway_transaction is not None:
            self.eway_transaction = eway_trans

    def __repr__(self):
        return '<CardTransaction({0}): {1} item(s)>'.format(
            self.object_id,
            self.items.count()
        )

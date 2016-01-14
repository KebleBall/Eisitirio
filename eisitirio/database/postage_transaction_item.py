# coding: utf-8
"""Database model for representing a ticket in a transaction."""

from __future__ import unicode_literals

from eisitirio.database import db
from eisitirio.database import transaction_item

DB = db.DB

class PostageTransactionItem(transaction_item.TransactionItem):
    """Model for representing a ticket in a transaction."""
    __tablename__ = 'postage_transaction_item'
    __mapper_args__ = {'polymorphic_identity': 'Postage'}

    object_id = DB.Column(
        DB.Integer(),
        DB.ForeignKey('transaction_item.object_id'),
        primary_key=True
    )

    is_refund = DB.Column(
        DB.Boolean,
        nullable=False,
        default=False
    )

    postage_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('postage.object_id'),
        nullable=False
    )
    postage = DB.relationship(
        'Postage',
        backref=DB.backref(
            'transaction_items',
            lazy='dynamic'
        )
    )

    def __init__(self, transaction, postage, is_refund=False):
        super(PostageTransactionItem, self).__init__(transaction, 'Postage')

        self.postage = postage
        self.is_refund = is_refund

    @property
    def value(self):
        """Get the value of this transaction item."""
        if self.is_refund:
            return 0 - self.postage.price
        else:
            return self.postage.price

    @property
    def description(self):
        """Get a description of the ticket with the type and guest name."""
        return '{0}{1} Postage'.format(
            'Refund of ' if self.is_refund else '',
            self.postage.postage_type
        )

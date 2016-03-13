# coding: utf-8
"""Database model for representing an admin fee in a transaction."""

from __future__ import unicode_literals

from eisitirio.database import db
from eisitirio.database import transaction_item

DB = db.DB

class AdminFeeTransactionItem(transaction_item.TransactionItem):
    """Model for representing an admin fee in a transaction."""
    __tablename__ = 'admin_fee_transaction_item'
    __mapper_args__ = {'polymorphic_identity': 'AdminFee'}

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

    admin_fee_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('admin_fee.object_id'),
        nullable=False
    )
    admin_fee = DB.relationship(
        'AdminFee',
        backref=DB.backref(
            'transaction_items',
            lazy='dynamic'
        )
    )

    def __init__(self, transaction, admin_fee, is_refund=False):
        super(AdminFeeTransactionItem, self).__init__(transaction, 'AdminFee')

        self.admin_fee = admin_fee
        self.is_refund = is_refund

    @property
    def value(self):
        """Get the value of this transaction item."""
        if self.is_refund:
            return 0 - self.admin_fee.amount
        else:
            return self.admin_fee.amount

    @property
    def description(self):
        """Get a description of the item."""
        return '{0} Admin Fee'.format(
            'Refund of ' if self.is_refund else ''
        )

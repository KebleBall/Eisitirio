# coding: utf-8
"""Database model for representing a ticket in a transaction."""

from __future__ import unicode_literals

from eisitirio.database import db
from eisitirio.database import transaction_item

DB = db.DB

class TicketTransactionItem(transaction_item.TransactionItem):
    """Model for representing a ticket in a transaction."""
    __tablename__ = 'ticket_transaction_item'
    __mapper_args__ = {'polymorphic_identity': 'Ticket'}

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

    ticket_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('ticket.object_id'),
        nullable=False
    )
    ticket = DB.relationship(
        'Ticket',
        backref=DB.backref(
            'transaction_items',
            lazy='dynamic'
        )
    )

    def __init__(self, transaction, ticket, is_refund=False):
        super(TicketTransactionItem, self).__init__(transaction, 'Ticket')

        self.ticket = ticket
        self.is_refund = is_refund

    @property
    def value(self):
        """Get the value of this transaction item."""
        if self.is_refund:
            return 0 - self.ticket.price
        else:
            return self.ticket.price

    @property
    def description(self):
        """Get a description of the ticket with the type and guest name."""
        return '{0}{1} Ticket ({2:05d})'.format(
            'Refund of ' if self.is_refund else '',
            self.ticket_type,
            self.ticket_id
        )

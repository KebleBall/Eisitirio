# coding: utf-8
"""Database model for tickets."""

from __future__ import unicode_literals

import datetime

from eisitirio import app
from eisitirio.database import db

APP = app.APP
DB = db.DB

class Ticket(DB.Model):
    """Model for tickets."""
    __tablename__ = 'ticket'

    ticket_type = DB.Column(
        DB.Unicode(50),
        nullable=False
    )

    paid = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )
    collected = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )
    entered = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )
    cancelled = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )

    price_ = DB.Column(
        DB.Integer(),
        nullable=False
    )
    name = DB.Column(
        DB.Unicode(120),
        nullable=True
    )
    note = DB.Column(
        DB.UnicodeText(),
        nullable=True
    )
    expires = DB.Column(
        DB.DateTime(),
        nullable=True
    )
    barcode = DB.Column(
        DB.Unicode(20),
        unique=True,
        nullable=True
    )

    owner_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=False
    )
    owner = DB.relationship(
        'User',
        backref=DB.backref(
            'tickets',
            lazy='dynamic',
            order_by=b'Ticket.cancelled'
        ),
        foreign_keys=[owner_id]
    )

    def __init__(self, owner, ticket_type, price):
        self.owner = owner
        self.ticket_type = ticket_type
        self.price = price

        self.expires = (datetime.datetime.utcnow() +
                        APP.config['TICKET_EXPIRY_TIME'])

    def __repr__(self):
        return '<Ticket {0} owned by {1} ({2})>'.format(
            self.object_id,
            self.owner.full_name,
            self.owner.object_id
        )

    @property
    def price_pounds(self):
        """Get the price of this ticket as a string of pounds and pence."""
        price = '{0:03d}'.format(self.price)
        return price[:-2] + '.' + price[-2:]

    @property
    def payment_method(self):
        """Get the payment method for this ticket."""
        if self.price == 0:
            return "Free"

        for transaction_item in self.transaction_items:
            if transaction_item.transaction.paid:
                return transaction_item.transaction.payment_method

        return "Unknown Payment Method"

    @property
    def price(self):
        """Get the price of the ticket."""
        return self.price_

    @price.setter
    def price(self, value):
        """Set the price of the ticket."""
        self.price_ = max(value, 0)

        if self.price_ == 0:
            self.mark_as_paid()

    def mark_as_paid(self):
        """Mark the ticket as paid, and clear any expiry."""
        self.paid = True
        self.expires = None

    def add_note(self, note):
        """Add a note to the ticket."""
        if not note.endswith('\n'):
            note = note + '\n'

        if self.note is None:
            self.note = note
        else:
            self.note = self.note + note

    @staticmethod
    def count():
        """How many tickets have been sold."""
        # TODO
        return Ticket.query.filter(Ticket.cancelled == False).count() # pylint: disable=singleton-comparison

    @staticmethod
    def write_csv_header(csv_writer):
        """Write the header of a CSV export file."""
        csv_writer.writerow([
            'Ticket ID',
            'Ticket Type',
            'Paid',
            'Collected',
            'Entered',
            'Cancelled',
            'Price (Pounds)',
            'Holder\'s Name',
            'Notes',
            'Expires',
            'Barcode',
            'Owner\' User ID',
            'Owner\'s Name',
        ])

    def write_csv_row(self, csv_writer):
        """Write this object as a row in a CSV export file."""
        csv_writer.writerow([
            self.object_id,
            self.ticket_type,
            'Yes' if self.paid else 'No',
            'Yes' if self.collected else 'No',
            'Yes' if self.entered else 'No',
            'Yes' if self.cancelled else 'No',
            self.price_pounds,
            self.name,
            self.note,
            self.expires.strftime(
                '%Y-%m-%d %H:%M:%S'
            ) if self.expires is not None else 'N/A',
            self.barcode if self.barcode is not None else 'N/A',
            self.owner_id,
            self.owner.full_name,
        ])

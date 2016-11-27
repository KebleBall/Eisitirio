# coding: utf-8
"""Database model for representing a 'roundup' donation"""

from __future__ import unicode_literals

from eisitirio.database import db

DB = db.DB

class RoundupDonation(DB.Model):
    """Model for representing a roundup donation"""
    __tablename__ = 'roundup_donation'

    base_donation_amt = DB.Column(
        DB.Integer(),
        nullable = False
    )

    total_amount = DB.Column(
        DB.Integer(),
        nullable = False
    )

    charged_to_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable = False
    )

    charged_to = DB.relationship(
        'User',
        backref = DB.backref(
            'roundup_donation',
            lazy = 'dynamic'
        ),
        foreign_keys=[charged_to_id]
    )

    def __init__(self, amount, charged_to):
        # Internal representaion of amt is integer. So need to multiply by
        # 100
        self.base_donation_amt = amount
        self.charged_to = charged_to
        self.total_amount = 0

    def __repr__(self):
        return '<RoundupDonation {0}:'
        return '<RoundupDonation {0}: £{1}>'.format(self.object_id, self.amount_pounds)

    @property
    def amount_pounds(self):
        """Get the fee amount as a string of pounds and pence."""
        amount = '{0:03d}'.format(self.total_amount)
        return amount[:-2] + '.' + amount[-2:]

    def apply(self, tickets):
        """Apply the roundup donation to a set of tickets
        """
        return [self.apply_to_ticket(t) for t in tickets]

    def apply_to_ticket(self, ticket):
        # TODO: Make sure that this is correct (it looks like the prices
        # are being represented by an int that is multiplied by 10???)
        ticket.price = ticket.price + self.base_donation_amt
        self.total_amount = self.total_amount + self.base_donation_amt
        ticket.add_note('Roundup donation amt {0}'.format(self.base_donation_amt))
        return ticket

# coding: utf-8
"""Database model for representing a 'roundup' donation"""

from __future__ import unicode_literals

from eisitiro import app
from eisitirio.database import db


APP = app.APP
DB = db.DB

class RoundupDonation(DB.model):
    """Model for representing a roundup donation"""
    __tablename_ = 'roundup_donation'

    amount = DB.Column(
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
        self.amount = amount
        self.charged_to = charged_to

    def __repr__(self):
        return '<RoundupDonation {0}:'
        return '<RoundupDonation {0}: £{1}>'.format(self.object_id, self.amount_pounds)

    @property
    def amount_pounds(self):
        """Get the fee amount as a string of pounds and pence."""
        amount = '{0:03d}'.format(self.amount)
        return amount[:-2] + '.' + amount[-2:]

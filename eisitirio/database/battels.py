# coding: utf-8
"""Database model for battels charges for current students."""

from __future__ import unicode_literals
from __future__ import division

from eisitirio import app
from eisitirio.database import db

DB = db.DB
APP = app.APP

class Battels(DB.Model):
    """Model for battels charges for current students."""
    __tablename__ = 'battels'

    battels_id = DB.Column(
        DB.Unicode(10),
        unique=True,
        nullable=True
    )
    email = DB.Column(
        DB.Unicode(120),
        unique=True,
        nullable=True
    )
    title = DB.Column(
        DB.Unicode(10),
        nullable=True
    )
    surname = DB.Column(
        DB.Unicode(60),
        nullable=True
    )
    forenames = DB.Column(
        DB.Unicode(60),
        nullable=True
    )
    michaelmas_charge = DB.Column(
        DB.Integer(),
        default=0,
        nullable=False
    )
    hilary_charge = DB.Column(
        DB.Integer(),
        default=0,
        nullable=False
    )
    manual = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )

    def __init__(
            self,
            battelsid=None,
            email=None,
            title=None,
            surname=None,
            forenames=None,
            manual=False
    ):
        self.battelsid = battelsid
        self.email = email
        self.title = title
        self.surname = surname
        self.forenames = forenames
        self.manual = manual

    def __repr__(self):
        return '<Battels {0}: {1}>'.format(self.object_id, self.battelsid)

    @property
    def michaelmas_charge_pounds(self):
        """Get the amount charged in Michaelmas as a pounds/pence string."""
        michaelmas_charge = '{0:03d}'.format(self.michaelmas_charge)
        return michaelmas_charge[:-2] + '.' + michaelmas_charge[-2:]

    @property
    def hilary_charge_pounds(self):
        """Get the amount charged in Hilary as a pounds/pence string."""
        hilary_charge = '{0:03d}'.format(self.hilary_charge)
        return hilary_charge[:-2] + '.' + hilary_charge[-2:]

    def charge(self, amount, term):
        """Apply a charge to this battels account."""
        if term == 'MTHT':
            # Integer division fails for negative numbers (i.e. refunds), as the
            # number is rounded the wrong way. Instead, we do floating point
            # division, and truncate.
            half = int(amount / 2.0)

            self.michaelmas_charge += half
            self.hilary_charge += amount - half
        elif term == 'MT':
            self.michaelmas_charge += amount
        elif term == 'HT':
            self.hilary_charge += amount
        else:
            raise ValueError(
                'Term "{0}" cannot be charged to battels'.format(
                    term
                )
            )

    def refund(self, amount, term):
        """Refund a ticket and mark it as cancelled."""
        if APP.config['CURRENT_TERM'] == 'MT':
            if term == 'MTHT':
                half = amount // 2

                self.michaelmas_charge -= half
                self.hilary_charge -= amount - half
            elif term == 'MT':
                self.michaelmas_charge -= amount
            elif term == 'HT':
                self.hilary_charge -= amount
        elif APP.config['CURRENT_TERM'] == 'HT':
            self.hilary_charge -= amount
        else:
            raise ValueError(
                'Can\'t refund battels tickets in the current term'
            )

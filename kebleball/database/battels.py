# coding: utf-8
"""Database model for battels charges for Keble Students."""

from __future__ import unicode_literals

from kebleball import app
from kebleball.database import db

DB = db.DB
APP = app.APP

class Battels(DB.Model):
    """Model for battels charges for Keble Students."""
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    battelsid = DB.Column(
        DB.Unicode(6),
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

    def __getattr__(self, name):
        """Magic method to generate amounts charged in pounds."""
        if name == 'mt_pounds':
            michaelmas_charge = '{0:03d}'.format(self.michaelmas_charge)
            return michaelmas_charge[:-2] + '.' + michaelmas_charge[-2:]
        elif name == 'ht_pounds':
            hilary_charge = '{0:03d}'.format(self.hilary_charge)
            return hilary_charge[:-2] + '.' + hilary_charge[-2:]
        else:
            raise AttributeError(
                'Battels instance has no attribute "{0}"'.format(name)
            )

    def charge(self, ticket, term, wholepounds=False):
        """Apply a charge to this battels account."""
        if term == 'MTHT':
            if wholepounds:
                half = ((ticket.price // 200) * 100)
            else:
                half = (ticket.price / 2)

            self.michaelmas_charge = self.michaelmas_charge + half
            self.hilary_charge = self.hilary_charge + (ticket.price - half)
        elif term == 'MT':
            self.michaelmas_charge = self.michaelmas_charge + ticket.price
        elif term == 'HT':
            self.hilary_charge = self.hilary_charge + ticket.price
        else:
            raise ValueError(
                'Term "{0}" cannot be charged to battels'.format(
                    term
                )
            )

        ticket.mark_as_paid(
            'Battels',
            'Battels {0}, {1} term'.format(
                'manual' if self.manual else self.battelsid,
                term
            ),
            battels_term=term,
            battels=self
        )

    def cancel(self, ticket):
        """Refund a ticket and mark it as cancelled."""
        if APP.config['CURRENT_TERM'] == 'MT':
            if ticket.battels_term == 'MTHT':
                self.michaelmas_charge = (
                    self.michaelmas_charge -
                    (ticket.price / 2)
                )

                self.hilary_charge = (
                    self.hilary_charge -
                    (
                        ticket.price -
                        (ticket.price / 2)
                    )
                )
            elif ticket.battels_term == 'MT':
                self.michaelmas_charge = self.michaelmas_charge - ticket.price
            elif ticket.battels_term == 'HT':
                self.hilary_charge = self.hilary_charge - ticket.price
        elif APP.config['CURRENT_TERM'] == 'HT':
            self.hilary_charge = self.hilary_charge - ticket.price
        else:
            raise ValueError(
                'Can\'t refund battels tickets in the current term'
            )

        ticket.cancelled = True
        DB.session.commit()

    @staticmethod
    def get_by_id(object_id):
        """Get a battels object by its database ID."""
        battels = Battels.query.filter(
            Battels.object_id == int(object_id)
        ).first()

        if not battels:
            return None

        return battels

    @staticmethod
    def get_by_battelsid(battelsid):
        """Get a college object by its college battels ID."""
        battels = Battels.query.filter(Battels.battelsid == battelsid).first()

        if not battels:
            return None

        return battels

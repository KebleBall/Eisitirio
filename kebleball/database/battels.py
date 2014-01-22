# coding: utf-8
"""
battels.py

Contains Battels class
Used to manage Battels charges
"""

from kebleball.database import db
from kebleball.app import app

class Battels(db.Model):
    id = db.Column(
        db.Integer(),
        primary_key=True,
        nullable=False
    )
    battelsid = db.Column(
        db.String(6),
        unique=True,
        nullable=True
    )
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=True
    )
    title = db.Column(
        db.String(10),
        nullable=True
    )
    surname = db.Column(
        db.String(60),
        nullable=True
    )
    forenames = db.Column(
        db.String(60),
        nullable=True
    )
    mt = db.Column(
        db.Integer(),
        default=0,
        nullable=False
    )
    ht = db.Column(
        db.Integer(),
        default=0,
        nullable=False
    )
    manual = db.Column(
        db.Boolean(),
        default=False,
        nullable=False
    )

    def __init__(
        self,
        battelsid = None,
        email = None,
        title = None,
        surname = None,
        forenames = None,
        manual = False
    ):
        self.battelsid = battelsid
        self.email = email
        self.title = title
        self.surname = surname
        self.forenames = forenames
        self.manual = manual

    def __repr__(self):
        return "<Battels {0}: {1}>".format(self.id, self.battelsid)

    def __getattr__(self, name):
        if name == 'mt_pounds':
            mt = '{0:03d}'.format(self.mt)
            return mt[:-2] + '.' + mt[-2:]
        elif name == 'ht_pounds':
            ht = '{0:03d}'.format(self.ht)
            return ht[:-2] + '.' + ht[-2:]
        else:
            raise AttributeError(
                "Battels instance has no attribute '{0}'".format(name)
            )

    def charge(self, ticket, term, wholepounds=False):
        if term == 'MTHT':
            if wholepounds:
                half = ((ticket.price // 200) * 100)
            else:
                half = (ticket.price / 2)

            self.mt = self.mt + half
            self.ht = self.ht + (ticket.price - half)
        elif term == 'MT':
            self.mt = self.mt + ticket.price
        elif term == 'HT':
            self.ht = self.ht + ticket.price
        else:
            raise ValueError(
                "Term '{0}' cannot be charged to battels".format(
                    term
                )
            )

        ticket.markAsPaid(
            'Battels',
            'Battels {0}, {1} term'.format(
                'manual' if self.manual else self.battelsid,
                term
            ),
            battels_term=term,
            battels=self
        )

    def cancel(self, ticket):
        if app.config['CURRENT_TERM'] == 'MT':
            if ticket.battels_term == 'MTHT':
                self.mt = self.mt - (ticket.price / 2)
                self.ht = self.ht - (ticket.price - (ticket.price / 2))
            elif term == 'MT':
                self.mt = self.mt - ticket.price
            elif term == 'HT':
                self.ht = self.ht - ticket.price
        elif app.config['CURRENT_TERM'] == 'HT':
            self.ht = self.ht - ticket.price
        else:
            raise ValueError("Can't refund battels tickets in the current term")

        ticket.cancelled = True
        db.session.commit()

    @staticmethod
    def get_by_id(id):
        battels = Battels.query.filter(Battels.id==int(id)).first()

        if not battels:
            return None

        return battels

    @staticmethod
    def get_by_battelsid(id):
        battels = Battels.query.filter(Battels.battelsid==int(id)).first()

        if not battels:
            return None

        return battels
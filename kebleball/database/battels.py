# coding: utf-8
"""Model for battels charges for Keble Students."""

from kebleball import database as db
from kebleball import app

DB = db.DB
APP = app.APP

class Battels(DB.Model):
    """Model for battels charges for Keble Students."""
    id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    battelsid = DB.Column(
        DB.String(6),
        unique=True,
        nullable=True
    )
    email = DB.Column(
        DB.String(120),
        unique=True,
        nullable=True
    )
    title = DB.Column(
        DB.String(10),
        nullable=True
    )
    surname = DB.Column(
        DB.String(60),
        nullable=True
    )
    forenames = DB.Column(
        DB.String(60),
        nullable=True
    )
    mt = DB.Column(
        DB.Integer(),
        default=0,
        nullable=False
    )
    ht = DB.Column(
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
        return "<Battels {0}: {1}>".format(self.id, self.battelsid)

    def __getattr__(self, name):
        """Magic method to generate amounts charged in pounds."""
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
        """Apply a charge to this battels account."""
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
                self.mt = self.mt - (ticket.price / 2)
                self.ht = self.ht - (ticket.price - (ticket.price / 2))
            elif ticket.battels_term == 'MT':
                self.mt = self.mt - ticket.price
            elif ticket.battels_term == 'HT':
                self.ht = self.ht - ticket.price
        elif APP.config['CURRENT_TERM'] == 'HT':
            self.ht = self.ht - ticket.price
        else:
            raise ValueError("Can't refund battels tickets in the current term")

        ticket.cancelled = True
        DB.session.commit()

    @staticmethod
    def get_by_id(id):
        """Get a battels object by its database ID."""
        battels = Battels.query.filter(Battels.id == int(id)).first()

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

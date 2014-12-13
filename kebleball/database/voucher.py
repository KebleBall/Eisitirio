# coding: utf-8
"""
voucher.py

Contains Voucher class
Used to store data about discount vouchers
"""

from kebleball.database import db
from datetime import datetime, timedelta

DB = db.DB

class Voucher(DB.Model):
    id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    code = DB.Column(
        DB.String(30),
        nullable=False
    )
    expires = DB.Column(
        DB.DateTime(),
        nullable=True
    )
    discounttype = DB.Column(
        DB.Enum(
            'Fixed Price',
            'Fixed Discount',
            'Percentage Discount'
        ),
        nullable=False
    )
    discountvalue = DB.Column(
        DB.Integer(),
        nullable=False
    )
    appliesto = DB.Column(
        DB.Enum(
            'Ticket',
            'Transaction'
        ),
        nullable=False
    )
    singleuse = DB.Column(
        DB.Boolean(),
        nullable=False
    )
    used = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=True
    )

    used_by_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.id'),
        nullable=True
    )
    used_by = DB.relationship(
        'User',
        backref=DB.backref(
            'vouchers_used',
            lazy='dynamic'
        )
    )

    def __init__(
            self,
            code,
            expires,
            discounttype,
            discountvalue,
            appliesto,
            singleuse
    ):
        if discounttype not in [
                'Fixed Price',
                'Fixed Discount',
                'Percentage Discount'
        ]:
            raise ValueError(
                '{0} is not a valid discount type'.format(discounttype)
            )

        if appliesto not in [
                'Ticket',
                'Transaction'
        ]:
            raise ValueError(
                '{0} is not a valid application'.format(appliesto)
            )

        self.code = code
        self.discounttype = discounttype
        self.discountvalue = discountvalue
        self.appliesto = appliesto
        self.singleuse = singleuse

        if isinstance(expires, timedelta):
            self.expires = datetime.utcnow() + expires
        else:
            self.expires = expires

    def __repr__(self):
        return '<Voucher: {0}/{1}>'.format(self.id, self.code)

    @staticmethod
    def get_by_code(code):
        return Voucher.query().filter_by(Voucher.code == code).first()

    def apply(self, tickets, user):
        if self.singleuse and self.used:
            return (False, tickets, 'Voucher has already been used.')

        if self.expires is not None and self.expires < datetime.utcnow():
            return (False, tickets, 'Voucher has expired.')

        self.used = True
        if self.singleuse:
            if hasattr(user, 'id'):
                self.used_by_id = user.id
            else:
                self.used_by_id = user

        if self.appliesto == 'Ticket':
            tickets[0] = self.apply_to_ticket(tickets[0])
            return (True, tickets, None)
        else:
            return (True, [self.apply_to_ticket(t) for t in tickets], None)

    def apply_to_ticket(self, ticket):
        if self.discounttype == 'Fixed Price':
            ticket.set_price(self.discountvalue)
        elif self.discounttype == 'Fixed Discount':
            ticket.set_price(ticket.price - self.discountvalue)
        else:
            ticket.set_price(ticket.price * (100 - self.discountvalue) / 100)

        ticket.add_note('Used voucher {0}/{1}'.format(self.id, self.code))

        return ticket

    @staticmethod
    def get_by_id(id):
        voucher = Voucher.query.filter(Voucher.id == int(id)).first()

        if not voucher:
            return None

        return voucher

# coding: utf-8
"""
voucher.py

Contains Voucher class
Used to store data about discount vouchers
"""

from kebleball.database import db
from kebleball.database.user import User
from datetime import datetime, timedelta

class Voucher(db.Model):
    id = db.Column(
        db.Integer(),
        primary_key=True,
        nullable=False
    )
    code = db.Column(
        db.String(30),
        nullable=False
    )
    expires = db.Column(
        db.DateTime(),
        nullable=True
    )
    discounttype = db.Column(
        db.Enum(
            'Fixed Price',
            'Fixed Discount',
            'Percentage Discount'
        ),
        nullable=False
    )
    discountvalue = db.Column(
        db.Integer(),
        nullable=False
    )
    appliesto = db.Column(
        db.Enum(
            'Ticket',
            'Transaction'
        ),
        nullable=False
    )
    singleuse = db.Column(
        db.Boolean(),
        nullable=False
    )
    used = db.Column(
        db.Boolean(),
        default=False,
        nullable=True
    )

    used_by_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True
    )
    used_by = db.relationship(
        'User',
        backref=db.backref(
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
    def getByCode(code):
        return Voucher.query().filter_by(Voucher.code==code).first()

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
            tickets[0] = self.applyToTicket(tickets[0])
            return (True, tickets, None)
        else:
            return (True, [self.applyToTicket(t) for t in tickets], None)

    def applyToTicket(self, ticket):
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
        voucher = Voucher.query.filter(Voucher.id==int(id)).first()

        if not voucher:
            return None

        return voucher

"""
voucher.py

Contains Voucher class
Used to store data about discount vouchers
"""

from kebleball.database import db
from datetime import datetime, timedelta

class Ticket(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(30))
    expires = db.Column(db.DateTime(), nullable=True)
    discounttype = db.Column(
        db.Enum(
            'Fixed Price',
            'Fixed Discount',
            'Percentage Discount'
        )
    )
    discountvalue = db.Column(db.Integer())
    appliesto = db.Column(
        db.Enum(
            'Ticket',
            'Transaction'
        )
    )
    singleuse = db.Column(db.Boolean())
    used = db.Column(db.Boolean(), default=False)

    used_by_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
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
        if self.used:
            return (False, tickets, 'Voucher has already been used.')

        if self.expires < datetime.utcnow():
            return (False, tickets, 'Voucher has expired.')

        if self.singleuse:
            self.used = True
            if isinstance(user, (int,long)):
                self.used_by_id = user
            else:
                self.used_by = user

        if self.appliesto == 'Ticket':
            tickets[0] = self.applyToTicket(tickets[0])
            return (True, tickets, None)
        else:
            return (True, [self.applyToTicket(t) for t in tickets], None)

    def applyToTicket(self, ticket):
        if self.discounttype == 'Fixed Price':
            ticket.price = self.discountvalue
        elif self.discounttype == 'Fixed Discount':
            ticket.price = max(ticket.price - self.discountvalue, 0)
        else:
            ticket.price = ticket.price * (100 - self.discountvalue) / 100

        return ticket
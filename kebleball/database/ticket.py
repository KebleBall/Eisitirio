"""
ticket.py

Contains Ticket class
Used to store data about tickets purchased
"""

from kebleball.database import db
from kebleball.database.user import User
from datetime import datetime
from kebleball.app import app
from kebleball.helpers import generate_key

class Ticket(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    paid = db.Column(db.Boolean(), default=False, nullable=False)
    collected = db.Column(db.Boolean(), default=False, nullable=False)
    cancelled = db.Column(db.Boolean(), default=False, nullable=False)
    paymentmethod = db.Column(
        db.Enum(
            'Battels',
            'Card',
            'Cash',
            'Cheque',
            'Free'
        ),
        nullable=True
    )
    paymentreference = db.Column(db.String(20), nullable=True)
    price = db.Column(db.Integer(), nullable=False)
    name = db.Column(db.String(120), nullable=True)
    note = db.Column(db.Text(), nullable=True)
    expires = db.Column(db.DateTime(), nullable=True)

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    owner = db.relationship(
        'User',
        backref=db.backref(
            'tickets',
            lazy='dynamic'
        ),
        foreign_keys=[owner_id]
    )

    resalekey = db.Column(db.String(32), nullable=True)
    resaleconfirmed = db.Column(db.Boolean(), default=False, nullable=False)
    reselling_to_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True
    )
    reselling_to = db.relationship(
        'User',
        backref=db.backref(
            'resales',
            lazy='dynamic'
        ),
        foreign_keys=[reselling_to_id]
    )

    referrer_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True
    )
    referrer = db.relationship(
        'User',
        backref=db.backref(
            'referrals',
            lazy='dynamic'
        ),
        foreign_keys=[referrer_id]
    )

    def __init__(self, owner, paymentmethod, price=None):
        if hasattr(owner, 'id'):
            self.owner_id = owner.id
        else:
            self.owner_id = owner

        self.paymentmethod = paymentmethod

        self.expires = datetime.utcnow() + app.config['TICKET_EXPIRY_TIME']

        if price is not None:
            self.setPrice(price)
        else:
            self.setPrice(app.config['TICKET_PRICE'])

    def __getattr__(self, name):
        if name == 'price_pounds':
            price = '{0:03d}'.format(self.price)
            return price[:-2] + '.' + price[-2:]
        else:
            raise AttributeError(
                "Ticket instance has no attribute '{0}'".format(name)
            )

    def __repr__(self):
        return '<Ticket {0} owned by {1} ({2})>'.format(
            self.id,
            self.owner.name,
            self.owner_id
        )

    def setPrice(self,price):
        price = max(price, 0)

        self.price = price

        if price == 0:
            self.markAsPaid('Free')

    def markAsPaid(self, method):
        if method not in [
            'Battels',
            'Card',
            'Cash',
            'Cheque',
            'Free'
        ]:
            raise ValueError(
                '{0} is not an acceptable payment method'.format(method)
            )

        self.paid = True
        self.paymentmethod = method
        self.expires = None

    def addNote(self, note):
        if not note.endswith('\n'):
            note = note + '\n'

        if self.note is None:
            self.note = note
        else:
            self.note = self.note + note

    def setReferrer(self, referrer):
        if hasattr(referrer, 'id'):
            self.referrer_id = referrer.id
        else:
            self.referrer_id = referrer

    def startResale(self, reselling_to):
        if hasattr(reselling_to, 'id'):
            self.reselling_to_id = reselling_to.id
        else:
            self.reselling_to_id = reselling_to

        self.resalekey = generate_key(32)
        self.resaleconfirmed = False

        # [todo] - Send email to reselling_to to confirm resale

    def cancelResale(self, key):
        if self.resalekey == key:
            self.reselling_to_id = None
            self.reselling_to = None
            self.resalekey = None
            self.resaleconfirmed = False
            return True
        else:
            return False

    def confirmResale(self, key):
        if self.resalekey == key:
            self.resaleconfirmed = True
            self.resalekey = generate_key(32)

            # [todo] - Send email to owner to complete resale

            return True
        else:
            return False

    def completeResale(self, key):
        if self.resalekey == key:
            self.addNote(
                'Resold by {0}/{1} to {2}/{3}'.format(
                    self.owner.id,
                    self.owner.name,
                    self.reselling_to.id,
                    self.reselling_to.name
                )
            )
            self.owner = self.reselling_to
            self.reselling_to_id = None
            self.reselling_to = None
            self.resalekey = None
            self.resaleconfirmed = False

            return True
        else:
            return False

    def cancel(self):
        # [todo] - Implement ticket.cancel

        raise NotImplementedError

    @classmethod
    def count(self):
        return Ticket.query.filter(Ticket.cancelled==False).count()
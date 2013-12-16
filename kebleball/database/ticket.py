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
    paid = db.Column(db.Boolean(), default=False)
    collected = db.Column(db.Boolean(), default=False)
    cancelled = db.Column(db.Boolean(), default=False)
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
    price = db.Column(db.Integer())
    name = db.Column(db.String(120), nullable=True)
    expires = db.Column(db.DateTime(), nullable=True)

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
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
    resaleconfirmed = db.Column(db.Boolean(), default=False)
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

    def __init__(self, owner, price, name=None):
        if isinstance(owner, User):
            self.owner = owner
        else:
            self.owner_id = owner

        self.price = price

        if price == 0:
            self.paid = True
            self.paymentmethod = 'Free'

        self.name = name

        self.expires = datetime.utcnow() + app.config['TICKET_EXPIRY_TIME']

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

    def startResale(self, reselling_to):
        if isinstance(reselling_to, User):
            self.reselling_to = reselling_to
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
            self.owner = self.reselling_to
            self.reselling_to_id = None
            self.reselling_to = None
            self.resalekey = None
            self.resaleconfirmed = False

            return True
        else:
            return False
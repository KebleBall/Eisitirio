# coding: utf-8
"""
ticket.py

Contains Ticket class
Used to store data about tickets purchased
"""

from kebleball.database import db
from kebleball.database.battels import Battels
from kebleball.database.user import User
from kebleball.database.card_transaction import CardTransaction
from datetime import datetime
from kebleball.app import app
from kebleball.helpers import generate_key

from flask import url_for, flash
from flask.ext.login import current_user

import re

ticket_transaction_link = db.Table(
    'ticket_transaction_link',
    db.Model.metadata,
    db.Column('ticket_id',
        db.Integer,
        db.ForeignKey('ticket.id')
    ),
    db.Column('transaction_id',
        db.Integer,
        db.ForeignKey('card_transaction.id')
    )
)

class Ticket(db.Model):
    id = db.Column(
        db.Integer(),
        primary_key=True,
        nullable=False
    )
    paid = db.Column(
        db.Boolean(),
        default=False,
        nullable=False
    )
    collected = db.Column(
        db.Boolean(),
        default=False,
        nullable=False
    )
    cancelled = db.Column(
        db.Boolean(),
        default=False,
        nullable=False
    )
    resold = db.Column(
        db.Boolean(),
        default=False,
        nullable=False
    )
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
    paymentreference = db.Column(
        db.String(50),
        nullable=True
    )
    price = db.Column(
        db.Integer(),
        nullable=False
    )
    name = db.Column(
        db.String(120),
        nullable=True
    )
    note = db.Column(
        db.Text(),
        nullable=True
    )
    expires = db.Column(
        db.DateTime(),
        nullable=True
    )
    resalekey = db.Column(
        db.String(32),
        nullable=True
    )
    resaleconfirmed = db.Column(
        db.Boolean(),
        nullable=True
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    owner = db.relationship(
        'User',
        backref=db.backref(
            'tickets',
            lazy='dynamic',
            order_by='Ticket.cancelled'
        ),
        foreign_keys=[owner_id]
    )

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

    transactions = db.relationship(
        'CardTransaction',
        secondary=ticket_transaction_link,
        backref='tickets'
    )

    card_transaction_id = db.Column(
        db.Integer,
        db.ForeignKey('card_transaction.id'),
        nullable=True
    )
    card_transaction = db.relationship(
        'CardTransaction',
        foreign_keys=[card_transaction_id]
    )

    battels_term = db.Column(db.String(4), nullable=True)
    battels_id = db.Column(
        db.Integer,
        db.ForeignKey('battels.id'),
        nullable=True
    )
    battels = db.relationship(
        'Battels',
        backref=db.backref(
            'tickets',
            lazy='dynamic'
        ),
        foreign_keys=[battels_id]
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
        return '<Ticket {0} owned by {1} {2} ({3})>'.format(
            self.id,
            self.owner.firstname,
            self.owner.surname,
            self.owner_id
        )

    def setPrice(self,price):
        price = max(price, 0)

        self.price = price

        if price == 0:
            self.markAsPaid('Free')

    def setPaymentMethod(self, method, reason=None):
        if method in ['Cash','Cheque']:
            self.addNote(
                method +
                ' payment reason: ' +
                reason
            )

        self.paymentmethod = method

    def markAsPaid(self, method, reference, **kwargs):
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
        self.paymentreference = reference
        self.expires = None

        if 'transaction' in kwargs:
            if hasattr(kwargs['transaction'], 'id'):
                self.card_transaction_id = kwargs['transaction'].id
            else:
                self.card_transaction_id = kwargs['transaction']

        if 'battels' in kwargs:
            if hasattr(kwargs['battels'], 'id'):
                self.battels_id = kwargs['battels'].id
            else:
                self.battels_id = kwargs['battels']

        if 'battels_term' in kwargs:
            self.battels_term = kwargs['battels_term']

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

    @staticmethod
    def startResale(tickets, reselling_to):
        if len(tickets) > 0:
            if hasattr(reselling_to, 'id'):
                id = reselling_to.id
            else:
                id = reselling_to
                reselling_to = User.get_by_id(reselling_to)

            resalekey = generate_key(32)

            for ticket in tickets:
                ticket.reselling_to_id = id
                ticket.resalekey = resalekey
                ticket.resaleconfirmed = False

            db.session.commit()

            app.log_manager.log_event(
                'Started Resale',
                tickets,
                current_user
            )

            app.email_manager.sendTemplate(
                reselling_to.email,
                "Confirm Ticket Resale",
                "confirmResale.email",
                confirmurl=url_for(
                    'resale.resaleConfirm',
                    resale_from=current_user.id,
                    resale_to=id,
                    key=resalekey,
                    _external=True
                ),
                cancelurl=url_for(
                    'resale.resaleCancel',
                    resale_from=current_user.id,
                    resale_to=id,
                    key=resalekey,
                    _external=True
                ),
                numTickets=len(tickets),
                resale_from=current_user
            )

            return True
        else:
            return False

    @staticmethod
    def cancelResale(resale_from, resale_to, key):
        tickets = Ticket.query \
            .filter(Ticket.owner_id == resale_from) \
            .filter(Ticket.reselling_to_id == resale_to) \
            .filter(Ticket.resalekey == key) \
            .all()

        if len(tickets) > 0:
            resale_from = tickets[0].owner
            resale_to = tickets[0].reselling_to

            if not (
                current_user == resale_to or
                current_user == resale_from
            ):
                flash(
                    u'You are not authorised to perform this action',
                    'error'
                )
                return False

            for ticket in tickets:
                ticket.reselling_to = None
                ticket.reselling_to_id = None
                ticket.resalekey = None
                ticket.resaleconfirmed = None

            db.session.commit()

            app.log_manager.log_event(
                'Cancelled Resale',
                tickets,
                current_user
            )

            app.email_manager.sendTemplate(
                resale_from.email,
                "Ticket Resale Cancelled",
                "ownerCancelResale.email",
                resale_to=resale_to
            )

            app.email_manager.sendTemplate(
                resale_to.email,
                "Ticket Resale Cancelled",
                "buyerCancelResale.email",
                resale_from=resale_from
            )

            return True
        else:
            return False

    @staticmethod
    def confirmResale(resale_from, resale_to, key):
        tickets = Ticket.query \
            .filter(Ticket.owner_id == resale_from) \
            .filter(Ticket.reselling_to_id == resale_to) \
            .filter(Ticket.resalekey == key) \
            .all()

        if len(tickets) > 0:
            resale_from = tickets[0].owner
            resale_to = tickets[0].reselling_to
            resalekey = generate_key(32)

            if current_user != resale_to:
                flash(
                    u'You are not authorised to perform this action',
                    'error'
                )
                return False

            for ticket in tickets:
                ticket.resalekey = resalekey
                ticket.resaleconfirmed = True

            db.session.commit()

            app.log_manager.log_event(
                'Confirmed Resale',
                tickets,
                current_user
            )

            app.email_manager.sendTemplate(
                resale_from.email,
                "Complete Ticket Resale",
                "completeResale.email",
                resale_to=resale_from,
                completeurl=url_for(
                    'resale.resaleComplete',
                    resale_from=resale_from.id,
                    resale_to=resale_to.id,
                    key=resalekey,
                    _external=True
                ),
                cancelurl=url_for(
                    'resale.resaleCancel',
                    resale_from=resale_from.id,
                    resale_to=resale_to.id,
                    key=resalekey,
                    _external=True
                ),
                numTickets=len(tickets)
            )

            return True
        else:
            return False

    @staticmethod
    def completeResale(resale_from, resale_to, key):
        tickets = Ticket.query \
            .filter(Ticket.owner_id == resale_from) \
            .filter(Ticket.reselling_to_id == resale_to) \
            .filter(Ticket.resalekey == key) \
            .filter(Ticket.resaleconfirmed == True) \
            .all()

        if len(tickets) > 0:
            resale_from = tickets[0].owner

            if current_user != resale_from:
                flash(
                    u'You are not authorised to perform this action',
                    'error'
                )
                return False

            for ticket in tickets:
                ticket.addNote(
                    'Resold by {0}/{1} to {2}/{3}'.format(
                        ticket.owner.id,
                        ticket.owner.name,
                        ticket.reselling_to.id,
                        ticket.reselling_to.name
                    )
                )
                ticket.owner = ticket.reselling_to
                ticket.reselling_to_id = None
                ticket.reselling_to = None
                ticket.resalekey = None
                ticket.name = None
                ticket.resold = True

            db.session.commit()

            app.log_manager.log_event(
                'Completed Resale',
                tickets,
                current_user
            )

            return True
        else:
            return False

    def canBeCancelledAutomatically(self):
        if self.cancelled:
            return False
        elif app.config['LOCKDOWN_MODE']:
            return False
        elif self.resalekey is not None:
            return False
        elif self.resold:
            return False
        elif not self.paid:
            return True
        elif self.paymentmethod == 'Card':
            return True
        elif self.paymentmethod == 'Battels':
            return (
                app.config['CURRENT_TERM'] != 'TT' and
                self.battels is not None and
                self.battels == self.owner.battels
            )
        elif self.paymentmethod == 'Free':
            return True
        else:
            return False

    def canChangeName(self):
        return not (
            app.config['LOCKDOWN_MODE'] or
            self.cancelled
        )

    @staticmethod
    def count():
        return Ticket.query.filter(Ticket.cancelled==False).count()

    @staticmethod
    def get_by_id(id):
        return Ticket.query.filter(Ticket.id == int(id)).first()
# coding: utf-8
"""Database model for tickets."""

from __future__ import unicode_literals

import datetime

from flask.ext import login
import flask

from kebleball import app
from kebleball import helpers
from kebleball.database import db

APP = app.APP
DB = db.DB

TICKET_TRANSACTION_LINK = DB.Table(
    'ticket_transaction_link',
    DB.Model.metadata,
    DB.Column(
        'ticket_id',
        DB.Integer,
        DB.ForeignKey('ticket.object_id')
    ),
    DB.Column(
        'transaction_id',
        DB.Integer,
        DB.ForeignKey('card_transaction.object_id')
    )
)

class Ticket(DB.Model):
    """Model for tickets."""
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    paid = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )
    collected = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )
    entered = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )
    barcode = DB.Column(
        DB.Unicode(20),
        unique=True,
        nullable=True
    )
    cancelled = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )
    resold = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )
    payment_method = DB.Column(
        DB.Enum(
            'Battels',
            'Card',
            'Cash',
            'Cheque',
            'Free'
        ),
        nullable=True
    )
    payment_reference = DB.Column(
        DB.Unicode(50),
        nullable=True
    )
    price = DB.Column(
        DB.Integer(),
        nullable=False
    )
    name = DB.Column(
        DB.Unicode(120),
        nullable=True
    )
    note = DB.Column(
        DB.UnicodeText(),
        nullable=True
    )
    expires = DB.Column(
        DB.DateTime(),
        nullable=True
    )
    resale_key = DB.Column(
        DB.Unicode(32),
        nullable=True
    )
    resaleconfirmed = DB.Column(
        DB.Boolean(),
        nullable=True
    )

    owner_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=False
    )
    owner = DB.relationship(
        'User',
        backref=DB.backref(
            'tickets',
            lazy='dynamic',
            order_by=b'Ticket.cancelled'
        ),
        foreign_keys=[owner_id]
    )

    reselling_to_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=True
    )
    reselling_to = DB.relationship(
        'User',
        backref=DB.backref(
            'resales',
            lazy='dynamic'
        ),
        foreign_keys=[reselling_to_id]
    )

    referrer_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=True
    )
    referrer = DB.relationship(
        'User',
        backref=DB.backref(
            'referrals',
            lazy='dynamic'
        ),
        foreign_keys=[referrer_id]
    )

    transactions = DB.relationship(
        'CardTransaction',
        secondary=TICKET_TRANSACTION_LINK,
        backref=DB.backref(
            'tickets',
            lazy='dynamic'
        ),
        lazy='dynamic'
    )

    card_transaction_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('card_transaction.object_id'),
        nullable=True
    )
    card_transaction = DB.relationship(
        'CardTransaction',
        foreign_keys=[card_transaction_id]
    )

    battels_term = DB.Column(DB.Unicode(4), nullable=True)
    battels_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('battels.object_id'),
        nullable=True
    )
    battels = DB.relationship(
        'Battels',
        backref=DB.backref(
            'tickets',
            lazy='dynamic'
        ),
        foreign_keys=[battels_id]
    )

    def __init__(self, owner, payment_method, price):
        if hasattr(owner, 'object_id'):
            self.owner_id = owner.object_id
        else:
            self.owner_id = owner

        self.payment_method = payment_method
        self.set_price(price)

        self.expires = (datetime.datetime.utcnow() +
                        app.config['TICKET_EXPIRY_TIME'])

    def __getattr__(self, name):
        """Magic method to generate ticket price in pounds."""
        if name == 'price_pounds':
            price = '{0:03d}'.format(self.price)
            return price[:-2] + '.' + price[-2:]
        else:
            raise AttributeError(
                'Ticket instance has no attribute "{0}"'.format(name)
            )

    def __repr__(self):
        return '<Ticket {0} owned by {1} ({2})>'.format(
            self.object_id,
            self.owner.full_name,
            self.owner_id
        )

    def set_price(self, price):
        """Set the price of the ticket."""
        price = max(price, 0)

        self.price = price

        if price == 0:
            self.mark_as_paid('Free', 'Free Ticket')

    def set_payment_method(self, method, reason=None):
        """Set the ticket's payment method."""
        if method in ['Cash', 'Cheque']:
            self.add_note(
                method +
                ' payment reason: ' +
                reason
            )

        self.payment_method = method

    def mark_as_paid(self, method, reference, **kwargs):
        """Mark the ticket as paid."""
        if method not in [
                'Battels',
                'Card',
                'Cash',
                'Cheque',
                'Free',
        ]:
            raise ValueError(
                '{0} is not an acceptable payment method'.format(method)
            )

        self.paid = True
        self.payment_method = method
        self.payment_reference = reference
        self.expires = None

        if 'transaction' in kwargs:
            if hasattr(kwargs['transaction'], 'object_id'):
                self.card_transaction_id = kwargs['transaction'].object_id
            else:
                self.card_transaction_id = kwargs['transaction']

        if 'battels' in kwargs:
            if hasattr(kwargs['battels'], 'object_id'):
                self.battels_id = kwargs['battels'].object_id
            else:
                self.battels_id = kwargs['battels']

        if 'battels_term' in kwargs:
            self.battels_term = kwargs['battels_term']

    def add_note(self, note):
        """Add a note to the ticket."""
        if not note.endswith('\n'):
            note = note + '\n'

        if self.note is None:
            self.note = note
        else:
            self.note = self.note + note

    def set_referrer(self, referrer):
        """Set who referred the user to buy this ticket."""
        if hasattr(referrer, 'object_id'):
            self.referrer_id = referrer.object_id
        else:
            self.referrer_id = referrer

    @staticmethod
    def start_resale(tickets, reselling_to):
        """Start the resale process for tickets."""
        if len(tickets) > 0:
            if hasattr(reselling_to, 'object_id'):
                object_id = reselling_to.object_id
            else:
                object_id = reselling_to
                reselling_to = DB.User.get_by_id(reselling_to)

            resale_key = helpers.generate_key(32)

            for ticket in tickets:
                ticket.reselling_to_id = object_id
                ticket.resale_key = resale_key
                ticket.resaleconfirmed = False

            DB.session.commit()

            app.log_manager.log_event(
                'Started Resale',
                tickets,
                login.current_user
            )

            app.email_manager.send_template(
                reselling_to.email,
                'Confirm Ticket Resale',
                'confirm_resale.email',
                confirmurl=flask.url_for(
                    'resale.resale_confirm',
                    resale_from=login.current_user.object_id,
                    resale_to=object_id,
                    key=resale_key,
                    _external=True
                ),
                cancelurl=flask.url_for(
                    'resale.resale_cancel',
                    resale_from=login.current_user.object_id,
                    resale_to=object_id,
                    key=resale_key,
                    _external=True
                ),
                num_tickets=len(tickets),
                resale_from=login.current_user
            )

            return True
        else:
            return False

    @staticmethod
    def cancel_resale(resale_from, resale_to, key):
        """Cancel the resale process."""
        tickets = Ticket.query.filter(
            Ticket.owner_id == resale_from
        ).filter(
            Ticket.reselling_to_id == resale_to
        ).filter(
            Ticket.resale_key == key
        ).all()

        if len(tickets) > 0:
            resale_from = tickets[0].owner
            resale_to = tickets[0].reselling_to

            if not (
                    login.current_user == resale_to or
                    login.current_user == resale_from
            ):
                flask.flash(
                    'You are not authorised to perform this action',
                    'error'
                )
                return False

            for ticket in tickets:
                ticket.reselling_to = None
                ticket.reselling_to_id = None
                ticket.resale_key = None
                ticket.resaleconfirmed = None

            DB.session.commit()

            app.log_manager.log_event(
                'Cancelled Resale',
                tickets,
                login.current_user
            )

            app.email_manager.send_template(
                resale_from.email,
                'Ticket Resale Cancelled',
                'owner_cancel_resale.email',
                resale_to=resale_to
            )

            app.email_manager.send_template(
                resale_to.email,
                'Ticket Resale Cancelled',
                'buyer_cancel_resale.email',
                resale_from=resale_from
            )

            return True
        else:
            return False

    @staticmethod
    def confirm_resale(resale_from, resale_to, key):
        """Confirm the resale.

        The resale is confirmed by the recipient before being completed by the
        owner of the ticket.
        """
        tickets = Ticket.query.filter(
            Ticket.owner_id == resale_from
        ).filter(
            Ticket.reselling_to_id == resale_to
        ).filter(
            Ticket.resale_key == key
        ).all()

        if len(tickets) > 0:
            resale_from = tickets[0].owner
            resale_to = tickets[0].reselling_to
            resale_key = helpers.generate_key(32)

            if login.current_user != resale_to:
                flask.flash(
                    'You are not authorised to perform this action',
                    'error'
                )
                return False

            for ticket in tickets:
                ticket.resale_key = resale_key
                ticket.resaleconfirmed = True

            DB.session.commit()

            app.log_manager.log_event(
                'Confirmed Resale',
                tickets,
                login.current_user
            )

            app.email_manager.send_template(
                resale_from.email,
                'Complete Ticket Resale',
                'complete_resale.email',
                resale_to=resale_to,
                completeurl=flask.url_for(
                    'resale.resale_complete',
                    resale_from=resale_from.object_id,
                    resale_to=resale_to.object_id,
                    key=resale_key,
                    _external=True
                ),
                cancelurl=flask.url_for(
                    'resale.resale_cancel',
                    resale_from=resale_from.object_id,
                    resale_to=resale_to.object_id,
                    key=resale_key,
                    _external=True
                ),
                num_tickets=len(tickets)
            )

            return True
        else:
            return False

    @staticmethod
    def complete_resale(resale_from, resale_to, key):
        """Complete the resale process.

        After the owner of the ticket is paid, the resale process is completed
        and the tickets are transferred to the new owner.
        """
        tickets = Ticket.query.filter(
            Ticket.owner_id == resale_from
        ).filter(
            Ticket.reselling_to_id == resale_to
        ).filter(
            Ticket.resale_key == key
        ).filter(
            Ticket.resaleconfirmed == True
        ).all()

        if len(tickets) > 0:
            resale_from = tickets[0].owner

            if login.current_user != resale_from:
                flask.flash(
                    'You are not authorised to perform this action',
                    'error'
                )
                return False

            for ticket in tickets:
                ticket.add_note(
                    'Resold by {0}/{1} to {2}/{3}'.format(
                        ticket.owner.object_id,
                        ticket.owner.full_name,
                        ticket.reselling_to.object_id,
                        ticket.reselling_to.full_name
                    )
                )
                ticket.owner = ticket.reselling_to
                ticket.reselling_to_id = None
                ticket.reselling_to = None
                ticket.resale_key = None
                ticket.name = None
                ticket.resold = True

            DB.session.commit()

            app.log_manager.log_event(
                'Completed Resale',
                tickets,
                login.current_user
            )

            return True
        else:
            return False

    def can_be_cancelled_automatically(self):
        """Check whether the ticket can be cancelled/refunded automatically."""
        if self.cancelled:
            return False
        elif app.config['LOCKDOWN_MODE']:
            return False
        elif self.collected:
            return False
        elif self.resale_key is not None:
            return False
        elif self.resold:
            return False
        elif not self.paid:
            return True
        elif self.payment_method == 'Card':
            return True
        elif self.payment_method == 'Battels':
            return (
                app.config['CURRENT_TERM'] != 'TT' and
                self.battels is not None and
                self.battels == self.owner.battels
            )
        elif self.payment_method == 'Free':
            return True
        else:
            return False

    def can_be_collected(self):
        """Check whether a ticket can be collected."""
        return (
            self.paid and
            not self.collected and
            not self.cancelled and
            self.name is not None
        )

    def can_be_resold(self):
        """Check whether a ticket can be resold."""
        return (
            self.paid and
            not self.collected and
            not self.cancelled and
            self.resale_key == None and
            not app.config['LOCKDOWN_MODE']
        )

    def can_change_name(self):
        """Check whether a ticket's name can be changed."""
        return not (
            app.config['LOCKDOWN_MODE'] or
            self.cancelled or
            self.collected
        )

    @staticmethod
    def count():
        """How many tickets have been sold."""
        return Ticket.query.filter(Ticket.cancelled == False).count()

    @staticmethod
    def get_by_id(object_id):
        """Get a ticket object by its database ID."""
        ticket = Ticket.query.filter(Ticket.object_id == int(object_id)).first()

        if not ticket:
            return None

        return ticket

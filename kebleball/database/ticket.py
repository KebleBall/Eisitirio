# coding: utf-8
"""Model for tickets."""

from datetime import datetime

from flask import url_for
from flask import flash
from flask.ext import login as flask_login

from kebleball.database import db
from kebleball import app
from kebleball.helpers import generate_key

APP = app.APP
DB = db.DB

TICKET_TRANSACTION_LINK = DB.Table(
    'ticket_transaction_link',
    DB.Model.metadata,
    DB.Column(
        'ticket_id',
        DB.Integer,
        DB.ForeignKey('ticket.id')
    ),
    DB.Column(
        'transaction_id',
        DB.Integer,
        DB.ForeignKey('card_transaction.id')
    )
)

class Ticket(DB.Model):
    """Model for tickets."""
    id = DB.Column(
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
        DB.String(20),
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
    paymentmethod = DB.Column(
        DB.Enum(
            'Battels',
            'Card',
            'Cash',
            'Cheque',
            'Free'
        ),
        nullable=True
    )
    paymentreference = DB.Column(
        DB.String(50),
        nullable=True
    )
    price = DB.Column(
        DB.Integer(),
        nullable=False
    )
    name = DB.Column(
        DB.String(120),
        nullable=True
    )
    note = DB.Column(
        DB.Text(),
        nullable=True
    )
    expires = DB.Column(
        DB.DateTime(),
        nullable=True
    )
    resalekey = DB.Column(
        DB.String(32),
        nullable=True
    )
    resaleconfirmed = DB.Column(
        DB.Boolean(),
        nullable=True
    )

    owner_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.id'),
        nullable=False
    )
    owner = DB.relationship(
        'User',
        backref=DB.backref(
            'tickets',
            lazy='dynamic',
            order_by='Ticket.cancelled'
        ),
        foreign_keys=[owner_id]
    )

    reselling_to_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.id'),
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
        DB.ForeignKey('user.id'),
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
        DB.ForeignKey('card_transaction.id'),
        nullable=True
    )
    card_transaction = DB.relationship(
        'CardTransaction',
        foreign_keys=[card_transaction_id]
    )

    battels_term = DB.Column(DB.String(4), nullable=True)
    battels_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('battels.id'),
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

    def __init__(self, owner, paymentmethod, price):
        if hasattr(owner, 'id'):
            self.owner_id = owner.id
        else:
            self.owner_id = owner

        self.paymentmethod = paymentmethod
        self.set_price(price)

        self.expires = datetime.utcnow() + app.config['TICKET_EXPIRY_TIME']

    def __getattr__(self, name):
        """Magic method to generate ticket price in pounds."""
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
            self.owner.fullname,
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

        self.paymentmethod = method

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
        if hasattr(referrer, 'id'):
            self.referrer_id = referrer.id
        else:
            self.referrer_id = referrer

    @staticmethod
    def start_resale(tickets, reselling_to):
        """Start the resale process for tickets."""
        if len(tickets) > 0:
            if hasattr(reselling_to, 'id'):
                id = reselling_to.id
            else:
                id = reselling_to
                reselling_to = DB.User.get_by_id(reselling_to)

            resalekey = generate_key(32)

            for ticket in tickets:
                ticket.reselling_to_id = id
                ticket.resalekey = resalekey
                ticket.resaleconfirmed = False

            DB.session.commit()

            app.log_manager.log_event(
                'Started Resale',
                tickets,
                flask_login.current_user
            )

            app.email_manager.sendTemplate(
                reselling_to.email,
                "Confirm Ticket Resale",
                "confirmResale.email",
                confirmurl=url_for(
                    'resale.resale_confirm',
                    resale_from=flask_login.current_user.id,
                    resale_to=id,
                    key=resalekey,
                    _external=True
                ),
                cancelurl=url_for(
                    'resale.resale_cancel',
                    resale_from=flask_login.current_user.id,
                    resale_to=id,
                    key=resalekey,
                    _external=True
                ),
                num_tickets=len(tickets),
                resale_from=flask_login.current_user
            )

            return True
        else:
            return False

    @staticmethod
    def cancel_resale(resale_from, resale_to, key):
        """Cancel the resale process."""
        tickets = Ticket.query \
            .filter(Ticket.owner_id == resale_from) \
            .filter(Ticket.reselling_to_id == resale_to) \
            .filter(Ticket.resalekey == key) \
            .all()

        if len(tickets) > 0:
            resale_from = tickets[0].owner
            resale_to = tickets[0].reselling_to

            if not (
                    flask_login.current_user == resale_to or
                    flask_login.current_user == resale_from
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

            DB.session.commit()

            app.log_manager.log_event(
                'Cancelled Resale',
                tickets,
                flask_login.current_user
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
    def confirm_resale(resale_from, resale_to, key):
        """Confirm the resale.

        The resale is confirmed by the recipient before being completed by the
        owner of the ticket.
        """
        tickets = Ticket.query \
            .filter(Ticket.owner_id == resale_from) \
            .filter(Ticket.reselling_to_id == resale_to) \
            .filter(Ticket.resalekey == key) \
            .all()

        if len(tickets) > 0:
            resale_from = tickets[0].owner
            resale_to = tickets[0].reselling_to
            resalekey = generate_key(32)

            if flask_login.current_user != resale_to:
                flash(
                    u'You are not authorised to perform this action',
                    'error'
                )
                return False

            for ticket in tickets:
                ticket.resalekey = resalekey
                ticket.resaleconfirmed = True

            DB.session.commit()

            app.log_manager.log_event(
                'Confirmed Resale',
                tickets,
                flask_login.current_user
            )

            app.email_manager.sendTemplate(
                resale_from.email,
                "Complete Ticket Resale",
                "completeResale.email",
                resale_to=resale_to,
                completeurl=url_for(
                    'resale.resale_complete',
                    resale_from=resale_from.id,
                    resale_to=resale_to.id,
                    key=resalekey,
                    _external=True
                ),
                cancelurl=url_for(
                    'resale.resale_cancel',
                    resale_from=resale_from.id,
                    resale_to=resale_to.id,
                    key=resalekey,
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
        tickets = Ticket.query \
            .filter(Ticket.owner_id == resale_from) \
            .filter(Ticket.reselling_to_id == resale_to) \
            .filter(Ticket.resalekey == key) \
            .filter(Ticket.resaleconfirmed == True) \
            .all()

        if len(tickets) > 0:
            resale_from = tickets[0].owner

            if flask_login.current_user != resale_from:
                flash(
                    u'You are not authorised to perform this action',
                    'error'
                )
                return False

            for ticket in tickets:
                ticket.add_note(
                    'Resold by {0}/{1} to {2}/{3}'.format(
                        ticket.owner.id,
                        ticket.owner.fullname,
                        ticket.reselling_to.id,
                        ticket.reselling_to.fullname
                    )
                )
                ticket.owner = ticket.reselling_to
                ticket.reselling_to_id = None
                ticket.reselling_to = None
                ticket.resalekey = None
                ticket.name = None
                ticket.resold = True

            DB.session.commit()

            app.log_manager.log_event(
                'Completed Resale',
                tickets,
                flask_login.current_user
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
            self.resalekey == None and
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
    def get_by_id(id):
        """Get a ticket object by its database ID."""
        ticket = Ticket.query.filter(Ticket.id == int(id)).first()

        if not ticket:
            return None

        return ticket

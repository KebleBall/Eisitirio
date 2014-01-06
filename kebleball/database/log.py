"""
log.py

Contains Log class
Used to store log entries
"""

from kebleball.database import db
from kebleball.database.user import User
from kebleball.database.ticket import Ticket
from kebleball.database.card_transaction import CardTransaction
from datetime import datetime

class Log(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime)
    ip = db.Column(db.String(45))
    action = db.Column(db.Text())

    actor_id = db.Column(
        db.Integer(),
        db.ForeignKey('user.id'),
        nullable=True
    )
    actor = db.relationship(
        User,
        backref=db.backref(
            'actions',
            lazy='dynamic'
        ),
        foreign_keys=[actor_id]
    )

    user_id = db.Column(
        db.Integer(),
        db.ForeignKey('user.id'),
        nullable=True
    )
    user = db.relationship(
        User,
        backref=db.backref(
            'events',
            lazy='dynamic'
        ),
        foreign_keys=[user_id]
    )

    ticket_id = db.Column(
        db.Integer(),
        db.ForeignKey('ticket.id'),
        nullable=True
    )
    ticket = db.relationship(
        Ticket,
        backref=db.backref(
            'events',
            lazy='dynamic'
        )
    )

    transaction_id = db.Column(
        db.Integer(),
        db.ForeignKey('card_transaction.id'),
        nullable=True
    )
    transaction = db.relationship(
        CardTransaction,
        backref=db.backref(
            'events',
            lazy='dynamic'
        )
    )

    def __init__(self, ip, action, actor, user, ticket=None, transaction=None):
        self.timestamp = datetime.utcnow()
        self.ip = ip
        self.action = action

        if hasattr(actor, 'id'):
            self.actor_id = actor.id
        else:
            self.actor_id = actor

        if hasattr(user, 'id'):
            self.user_id = user.id
        else:
            self.user_id = user

        if hasattr(ticket, 'id'):
            self.ticket_id = ticket.id
        else:
            self.ticket_id = ticket

        if hasattr(transaction, 'id'):
            self.transaction_id = transaction.id
        else:
            self.transaction_id = transaction

    def __repr__(self):
        return '<Log {0}: {1}>'.format(
            self.id,
            self.timestamp.strftime('%Y-%m-%d %H:%m (UTC)')
        )

    def display(self):
        return '{0}: {1} {2} acting as {3} {4}{5}{6} - {7}'.format(
            self.timestamp.strftime('%Y-%m-%d %H:%m (UTC)'),
            self.actor.firstname,
            self.actor.surname,
            self.user.firstname,
            self.user.surname,
            (
                "" if self.ticket is None else (
                    ", in relation "
                    "to ticket {0}"
                ).format(
                    self.ticket.id
                )
            ),
            (
                "" if self.transaction is None else (
                    ", in relation "
                    "to transaction {0}"
                ).format(
                    self.transaction.id
                )
            ),
            self.message
        )
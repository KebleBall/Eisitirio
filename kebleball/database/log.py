# coding: utf-8
"""
log.py

Contains Log class
Used to store log entries
"""

from kebleball.database import db
from kebleball.database import user
from kebleball.database import ticket
from kebleball.database import card_transaction
from datetime import datetime

DB = db.DB

User = user.User
Ticket = ticket.Ticket
CardTransaction = card_transaction.CardTransaction

LOG_TICKET_LINK = DB.Table(
    'log_ticket_link',
    DB.Model.metadata,
    DB.Column('log_id',
              DB.Integer,
              DB.ForeignKey('log.object_id')
             ),
    DB.Column('ticket_id',
              DB.Integer,
              DB.ForeignKey('ticket.object_id')
             )
)

class Log(DB.Model):
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    timestamp = DB.Column(
        DB.DateTime,
        nullable=False
    )
    ip = DB.Column(
        DB.String(45),
        nullable=False
    )
    action = DB.Column(DB.Text())

    actor_id = DB.Column(
        DB.Integer(),
        DB.ForeignKey('user.object_id'),
        nullable=True
    )
    actor = DB.relationship(
        User,
        backref=DB.backref(
            'actions',
            lazy='dynamic'
        ),
        foreign_keys=[actor_id]
    )

    user_id = DB.Column(
        DB.Integer(),
        DB.ForeignKey('user.object_id'),
        nullable=True
    )
    user = DB.relationship(
        User,
        backref=DB.backref(
            'events',
            lazy='dynamic'
        ),
        foreign_keys=[user_id]
    )

    tickets = DB.relationship(
        'Ticket',
        secondary=LOG_TICKET_LINK,
        backref=DB.backref(
            'log_entries',
            lazy='dynamic'
        ),
        lazy='dynamic'
    )

    transaction_id = DB.Column(
        DB.Integer(),
        DB.ForeignKey('card_transaction.object_id'),
        nullable=True
    )
    transaction = DB.relationship(
        CardTransaction,
        backref=DB.backref(
            'events',
            lazy='dynamic'
        )
    )

    def __init__(self, ip, action, actor, user, tickets=None, transaction=None):
        if tickets is None:
            tickets = []
        self.timestamp = datetime.utcnow()
        self.ip = ip
        self.action = action

        if hasattr(actor, 'object_id'):
            self.actor_id = actor.object_id
        else:
            self.actor_id = actor

        if hasattr(user, 'object_id'):
            self.user_id = user.object_id
        else:
            self.user_id = user

        for ticket in tickets:
            if hasattr(ticket, 'object_id'):
                self.tickets.append(ticket)
            else:
                self.tickets.append(Ticket.get_by_id(ticket))

        if hasattr(transaction, 'object_id'):
            self.transaction_id = transaction.object_id
        else:
            self.transaction_id = transaction

    def __repr__(self):
        return '<Log {0}: {1}>'.format(
            self.object_id,
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
                    "to {0} tickets"
                ).format(
                    self.tickets.count()
                )
            ),
            (
                "" if self.transaction is None else (
                    ", in relation "
                    "to transaction {0}"
                ).format(
                    self.transaction.object_id
                )
            ),
            self.message
        )

    @staticmethod
    def get_by_id(object_id):
        log = Log.query.filter(Log.object_id == int(object_id)).first()

        if not log:
            return None

        return log

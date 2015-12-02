# coding: utf-8
"""Database model for log entries persisted to the database."""

from __future__ import unicode_literals

import datetime

from eisitirio.database import db

DB = db.DB

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
    """Model for log entries persisted to the database."""
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    timestamp = DB.Column(
        DB.DateTime,
        nullable=False
    )
    ip_address = DB.Column(
        DB.Unicode(45),
        nullable=False
    )
    action = DB.Column(DB.UnicodeText())

    actor_id = DB.Column(
        DB.Integer(),
        DB.ForeignKey('user.object_id'),
        nullable=True
    )
    actor = DB.relationship(
        'User',
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
        'User',
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

    card_transaction_id = DB.Column(
        DB.Integer(),
        DB.ForeignKey('card_transaction.object_id'),
        nullable=True
    )
    card_transaction = DB.relationship(
        'CardTransaction',
        backref=DB.backref(
            'events',
            lazy='dynamic'
        )
    )

    def __init__(self, ip_address, action, actor, user, tickets=None,
                 card_transaction=None):
        if tickets is None:
            tickets = []

        self.timestamp = datetime.datetime.utcnow()
        self.ip_address = ip_address
        self.action = action
        self.actor = actor
        self.user = user
        self.tickets = tickets
        self.card_transaction = card_transaction

    def __repr__(self):
        return '<Log {0}: {1}>'.format(
            self.object_id,
            self.timestamp.strftime('%Y-%m-%d %H:%m (UTC)')
        )

    @staticmethod
    def get_by_id(object_id):
        """Get a Log object by its database ID."""
        log = Log.query.filter(Log.object_id == int(object_id)).first()

        if not log:
            return None

        return log

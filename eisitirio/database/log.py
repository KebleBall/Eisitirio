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
    __tablename__ = 'log'

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
    def write_csv_header(csv_writer):
        """Write the header of a CSV export file."""
        csv_writer.writerow([
            'Log Entry ID',
            'Timestamp',
            'IP Address',
            'Action',
            'Actor\'s User ID',
            'Actor\'s Name',
            'Target\'s User ID',
            'Target\'s Name',
            'Relevant Ticket IDs',
            'Relevant Card Transaction ID',
        ])

    def write_csv_row(self, csv_writer):
        """Write this object as a row in a CSV export file."""
        csv_writer.writerow([
            self.object_id,
            self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            self.ip_address,
            self.action,
            self.actor_id if self.actor_id is not None else 'N/A',
            self.actor if self.actor is not None else 'N/A',
            self.user_id if self.user_id is not None else 'N/A',
            self.user if self.user is not None else 'N/A',
            ','.join(str(ticket.object_id) for ticket in self.tickets),
            (
                self.card_transaction_id
                if self.card_transaction_id is not None
                else 'N/A'
            ),
        ])

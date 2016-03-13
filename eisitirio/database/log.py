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
            'events',
            lazy='dynamic'
        ),
        lazy='dynamic'
    )

    transaction_id = DB.Column(
        DB.Integer(),
        DB.ForeignKey('transaction.object_id'),
        nullable=True
    )
    transaction = DB.relationship(
        'Transaction',
        backref=DB.backref(
            'events',
            lazy='dynamic'
        )
    )

    purchase_group_id = DB.Column(
        DB.Integer(),
        DB.ForeignKey('purchase_group.object_id'),
        nullable=True
    )
    purchase_group = DB.relationship(
        'PurchaseGroup',
        backref=DB.backref(
            'events',
            lazy='dynamic'
        )
    )

    admin_fee_id = DB.Column(
        DB.Integer(),
        DB.ForeignKey('admin_fee.object_id'),
        nullable=True
    )
    admin_fee = DB.relationship(
        'AdminFee',
        backref=DB.backref(
            'events',
            lazy='dynamic'
        )
    )

    def __init__(self, ip_address, action, actor, user, tickets=None,
                 transaction=None, purchase_group=None, admin_fee=None):
        if tickets is None:
            tickets = []

        self.timestamp = datetime.datetime.utcnow()
        self.ip_address = ip_address
        self.action = action
        self.actor = actor
        self.user = user
        self.tickets = tickets
        self.transaction = transaction
        self.purchase_group = purchase_group
        self.admin_fee = admin_fee

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
            'Relevant Transaction ID',
            'Relevant Purchase Group ID',
            'Relevant Admin Fee ID',
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
                self.transaction_id
                if self.transaction_id is not None
                else 'N/A'
            ),
            (
                self.purchase_group_id
                if self.purchase_group_id is not None
                else 'N/A'
            ),
            (
                self.admin_fee_id
                if self.admin_fee_id is not None
                else 'N/A'
            ),
        ])

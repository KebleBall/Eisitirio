"""
log.py

Contains Log class
Used to store log entries
"""

from kebleball.database import db
from datetime import datetime

class Log(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime)
    ip = db.Column(db.String(45))
    action = db.Column(db.Text())

    actor_id = db.Column(
        db.Integer(),
        db.ForeignKey('user.id')
    )
    actor = db.relationship(
        'User',
        backref=db.backref(
            'actions',
            lazy='dynamic'
        )
    )

    user_id = db.Column(
        db.Integer(),
        db.ForeignKey('user.id')
    )
    user = db.relationship(
        'User',
        backref=db.backref(
            'events',
            lazy='dynamic'
        )
    )

    ticket_id = db.Column(
        db.Integer(),
        db.ForeignKey('ticket.id'),
        nullable=True
    )
    ticket = db.relationship(
        'Ticket',
        backref=db.backref(
            'events',
            lazy='dynamic'
        )
    )

    def __init__(self, ip, message, actor, user, ticket=None):
        self.timestamp = datetime.utcnow()
        self.ip = ip
        self.message = message

        if isinstance(actor, (int,long)):
            self.actor_id = actor
        else:
            self.actor = actor

        if isinstance(user, (int,long)):
            self.user_id = user
        else:
            self.user = user

        if isinstance(ticket, (int,long)):
            self.ticket_id = ticket
        else:
            self.ticket = ticket

    def __repr__(self):
        return '<Log {0}: {1}>'.format(
            self.id,
            self.timestamp.strftime('%Y-%m-%d %H:%m (UTC)')
        )

    def display(self):
        return '{0}: {1} acting as {2}{3} - {4}'.format(
            self.timestamp.strftime('%Y-%m-%d %H:%m (UTC)'),
            self.actor.name,
            self.user.name,
            (
                "" if self.ticket is None else ", in relation "
                "to ticket {0}".format(
                    self.ticket.id
                )
            ),
            self.message
        )
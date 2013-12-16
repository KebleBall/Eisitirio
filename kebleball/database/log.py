"""
log.py

Contains Log class
Used to store log entries
"""

from kebleball.database import db
from kebleball.database.user import User
from kebleball.database.ticket import Ticket
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
        User,
        backref=db.backref(
            'actions',
            lazy='dynamic'
        ),
        foreign_keys=[actor_id]
    )

    user_id = db.Column(
        db.Integer(),
        db.ForeignKey('user.id')
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

    def __init__(self, ip, message, actor, user, ticket=None):
        self.timestamp = datetime.utcnow()
        self.ip = ip
        self.message = message

        if isinstance(actor, User):
            self.actor = actor
        else:
            self.actor_id = actor

        if isinstance(user, User):
            self.user = user
        else:
            self.user_id = user

        if isinstance(ticket, Ticket):
            self.ticket = ticket
        else:
            self.ticket_id = ticket

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
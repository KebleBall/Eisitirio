# coding: utf-8
"""Database model for entries on the waiting list."""

from __future__ import unicode_literals

import datetime

from eisitirio.database import db

DB = db.DB

class Waiting(DB.Model):
    """Model for entries on the waiting list."""
    __tablename__ = 'waiting'

    waiting_since = DB.Column(
        DB.DateTime(),
        nullable=False
    )
    waiting_for = DB.Column(
        DB.Integer(),
        nullable=False
    )

    user_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=False
    )
    user = DB.relationship(
        'User',
        backref=DB.backref(
            'waiting',
            lazy='dynamic'
        ),
        foreign_keys=[user_id]
    )

    def __init__(self, user, waiting_for):
        self.user = user
        self.waiting_for = waiting_for

        self.waiting_since = datetime.datetime.utcnow()

    def __repr__(self):
        return '<Waiting: {0} for {1} ticket{2}>'.format(
            self.user.full_name,
            self.waiting_for,
            '' if self.waiting_for == 1 else 's'
        )

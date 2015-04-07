# coding: utf-8
"""Database model for entries on the waiting list."""

from __future__ import unicode_literals

import datetime

from kebleball.database import db

DB = db.DB

class Waiting(DB.Model):
    """Model for entries on the waiting list."""
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
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

    referrer_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=True
    )
    referrer = DB.relationship(
        'User',
        backref=DB.backref(
            'waiting_referrals',
            lazy='dynamic'
        ),
        foreign_keys=[referrer_id]
    )

    def __init__(self, user, waiting_for, referrer=None):
        if hasattr(user, 'object_id'):
            self.user_id = user.object_id
        else:
            self.user_id = user

        if hasattr(referrer, 'object_id'):
            self.referrer_id = referrer.object_id
        else:
            self.referrer_id = referrer

        self.waiting_for = waiting_for

        self.waiting_since = datetime.datetime.utcnow()

    def __repr__(self):
        return '<Waiting: {0} for {1} ticket{2}>'.format(
            self.user.full_name,
            self.waiting_for,
            '' if self.waiting_for == 1 else 's'
        )

    @staticmethod
    def get_by_id(object_id):
        """Get a waiting object by its database ID."""
        waiting = Waiting.query.filter(
            Waiting.object_id == int(object_id)
        ).first()

        if not waiting:
            return None

        return waiting

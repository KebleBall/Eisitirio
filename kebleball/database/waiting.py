# coding: utf-8
"""Model for entries on the waiting list."""

from datetime import datetime

from kebleball.database import db

DB = db.DB

class Waiting(DB.Model):
    """Model for entries on the waiting list."""
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    waitingsince = DB.Column(
        DB.DateTime(),
        nullable=False
    )
    waitingfor = DB.Column(
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

    def __init__(self, user, waitingfor, referrer=None):
        if hasattr(user, 'object_id'):
            self.user_id = user.object_id
        else:
            self.user_id = user

        if hasattr(referrer, 'object_id'):
            self.referrer_id = referrer.object_id
        else:
            self.referrer_id = referrer

        self.waitingfor = waitingfor

        self.waitingsince = datetime.utcnow()

    def __repr__(self):
        return '<Waiting: {0} {1} for {2} ticket{3}>'.format(
            self.user.firstname,
            self.user.surname,
            self.waitingfor,
            '' if self.waitingfor == 1 else 's'
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

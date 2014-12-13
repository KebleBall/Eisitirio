# coding: utf-8
"""Model for entries on the waiting list."""

from datetime import datetime

from kebleball.database import db

DB = db.DB

class Waiting(DB.Model):
    """Model for entries on the waiting list."""
    id = DB.Column(
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
        DB.ForeignKey('user.id'),
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
        DB.ForeignKey('user.id'),
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
        if hasattr(user, 'id'):
            self.user_id = user.id
        else:
            self.user_id = user

        if hasattr(referrer, 'id'):
            self.referrer_id = referrer.id
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
    def get_by_id(id):
        waiting = Waiting.query.filter(Waiting.id == int(id)).first()

        if not waiting:
            return None

        return waiting

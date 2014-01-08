# coding: utf-8
"""
waiting.py

Contains Waiting class
Used to store data about users waiting for tickets
"""

from kebleball.database import db
from kebleball.database.user import User
from datetime import datetime

class Waiting(db.Model):
    id = db.Column(
        db.Integer(),
        primary_key=True,
        nullable=False
    )
    waitingsince = db.Column(
        db.DateTime(),
        nullable=False
    )
    waitingfor = db.Column(
        db.Integer(),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    user = db.relationship(
        'User',
        backref=db.backref(
            'waiting',
            lazy='dynamic'
        ),
        foreign_keys=[user_id]
    )

    referrer_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True
    )
    referrer = db.relationship(
        'User',
        backref=db.backref(
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
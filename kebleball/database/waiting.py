"""
waiting.py

Contains Waiting class
Used to store data about users waiting for tickets
"""

from kebleball.database import db
from datetime import datetime

class Waiting(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    waitingsince = db.Column(db.DateTime())
    waitingfor = db.Column(db.Integer())

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )
    user = db.relationship(
        'User',
        backref=db.backref(
            'waiting',
            lazy='dynamic'
        )
    )

    def __init__(self, user, waitingfor):
        if isinstance(user, (int,long)):
            self.user_id = user
        else:
            self.user = user

        self.waitingfor = waitingfor

        self.waitingsince = datetime.utcnow()

    def __repr__(self):
        return '<Waiting: {0} for {1} ticket{2}>'.format(
            self.user.name,
            self.waitingfor,
            '' if self.waitingfor == 1 else 's'
        )
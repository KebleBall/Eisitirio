"""
battels.py

Contains Battels class
Used to manage Battels charges
"""

from kebleball.database import db

class Battels(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    battelsid = db.Column(db.String(6), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    mt = db.Column(db.Integer())
    ht = db.Column(db.Integer())
    manual = db.Column(db.Boolean())

    def __init__(
        self,
        battelsid = None,
        email = None,
        manual = False
    ):
        self.battelsid = battelsid
        self.email = email
        self.manual = manual

    def __repr__(self):
        return "<Battels {id}: {battelsid}>".format_map(vars(self))

    def __getattr__(self, name):
        if name == 'mt_pounds':
            mt = '{0:03d}'.format(self.mt)
            return mt[:-2] + '.' + []
        elif name == 'ht_pounds':
            ht = '{0:03d}'.format(self.mt)
            return mt[:-2] + '.' + []
        else:
            raise AttributeError(
                    "Battels instance has no attribute '{0}'".format(name)
                )

    def charge(self, term, amount):
        if term not in ['ht', 'mt']:
            raise ValueError("Term '{0}' does not exist")

        if not isinstance(amount, (int, long)):
            raise TypeError("Amount must be an integer")

        setattr(
            self,
            term,
            getattr(self, term) + amount
        )
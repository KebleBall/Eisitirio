# coding: utf-8
"""Database model for representing a battels transaction."""

from __future__ import unicode_literals

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import transaction

DB = db.DB
APP = app.APP

class BattelsTransaction(transaction.Transaction):
    """Model for representing a battels transaction."""
    __tablename__ = 'battels_transaction'
    __mapper_args__ = {'polymorphic_identity': 'Battels'}

    object_id = DB.Column(
        DB.Integer(),
        DB.ForeignKey('transaction.object_id'),
        primary_key=True
    )

    battels_term = DB.Column(
        DB.Unicode(4),
        nullable=True
    )

    def __init__(self, user):
        super(BattelsTransaction, self).__init__(user, 'Battels')

    def __repr__(self):
        return '<BattelsTransaction {0}: {1} item(s)>'.format(
            self.object_id,
            self.items.count()
        )

    def charge(self, term):
        """Charge this transaction to the user's battels account."""
        self.battels_term = term

        self.user.battels.charge(self.value, term)

        self.mark_as_paid()

        APP.log_manager.log_event(
            'Completed Battels Payment',
            tickets=self.tickets,
            user=self.user,
            transaction=self,
            commit=False
        )

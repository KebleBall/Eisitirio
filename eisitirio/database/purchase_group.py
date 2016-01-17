# coding: utf-8
"""Database model for a purchase group."""

from __future__ import unicode_literals

import collections

from eisitirio.database import db
from eisitirio.helpers import util

DB = db.DB

class PurchaseGroup(DB.Model):
    """Model for a purchase group to allow pooling allowances."""
    __tablename__ = 'purchase_group'

    code = DB.Column(
        DB.Unicode(10),
        unique=True,
        nullable=False
    )

    leader_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=False
    )
    leader = DB.relationship(
        'User',
        backref=DB.backref(
            'purchase_group',
            lazy=False,
            uselist=False
        )
    )

    def __init__(self, leader):
        self.leader = leader

        self.code = util.generate_key(10)

    @property
    def total_requested(self):
        return sum(request.number_requested for request in self.requests)

    @property
    def requested(self):
        """Get the total number of each type of ticket requested."""
        requests = collections.defaultdict(int)

        for request in self.requests:
            requests[request.ticket_type_slug] += request.number_requested

        return requests

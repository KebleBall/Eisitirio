# coding: utf-8
"""Database model for a purchase group."""

from __future__ import unicode_literals

from eisitirio.database import db
from eisitirio.helpers import util

DB = db.DB

GROUP_MEMBER_LINK = DB.Table(
    'purchase_group_member_link',
    DB.Model.metadata,
    DB.Column('group_id',
              DB.Integer,
              DB.ForeignKey('purchase_group.object_id')
             ),
    DB.Column('user_id',
              DB.Integer,
              DB.ForeignKey('user.object_id')
             )
)

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
        foreign_keys=[leader_id]
    )

    members = DB.relationship(
        'User',
        secondary=GROUP_MEMBER_LINK,
        backref=DB.backref(
            'purchase_group',
            lazy=False,
            uselist=False
        ),
        lazy='dynamic'
    )

    disbanded = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )
    purchased = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )

    def __init__(self, leader):
        self.leader = leader
        self.members = [leader]

        self.code = util.generate_key(10)

    def __repr__(self):
        return '<PurchaseGroup({0}): {1} tickets, £{2}>'.format(
            self.object_id,
            self.total_requested,
            self.total_value_pounds
        )

    @property
    def total_value(self):
        """Get the total value of tickets requested by this group in pence."""
        return sum(request.value for request in self.requests)

    @property
    def total_value_pounds(self):
        """Get the total value of this group in pounds and pence."""
        value = '{0:03d}'.format(self.total_value)

        return value[:-2] + '.' + value[-2:]

    @property
    def total_requested(self):
        """Get the total number of tickets requested by this group."""
        return sum(request.number_requested for request in self.requests)

    @property
    def total_guest_tickets_requested(self):
        """Get the total number of guest tickets requested by this group."""
        return sum(
            request.number_requested
            for request in self.requests
            if request.ticket_type.counts_towards_guest_limit
        )

    @staticmethod
    def get_by_code(code):
        """Get a purchase group object by its code."""
        group = PurchaseGroup.query.filter(PurchaseGroup.code == code).first()

        if not group:
            return None

        return group

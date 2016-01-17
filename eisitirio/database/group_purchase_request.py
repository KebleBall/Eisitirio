# coding: utf-8
"""Database model for a request for tickets in a group purchase."""

from __future__ import unicode_literals

from eisitirio.database import db

DB = db.DB

class GroupPurchaseRequest(DB.Model):
    """Model for a request for tickets in a group purchase."""
    __tablename__ = 'group_purchase_request'

    ticket_type_slug = DB.Column(
        DB.Unicode(50),
        nullable=False
    )
    number_requested = DB.Column(
        DB.Integer(),
        nullable=False
    )

    purchase_group_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('purchase_group.object_id'),
        nullable=False
    )
    purchase_group = DB.relationship(
        'PurchaseGroup',
        backref=DB.backref(
            'requests',
            lazy='dynamic'
        )
    )

    requester_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=False
    )
    requester = DB.relationship(
        'User',
        backref=DB.backref(
            'group_purchase_requests',
            lazy='dynamic'
        )
    )

    def __init__(self, ticket_type_slug, number_requested, purchase_group,
                 requester):
        self.ticket_type_slug = ticket_type_slug
        self.number_requested = number_requested
        self.purchase_group = purchase_group
        self.requester = requester

# coding: utf-8
"""Database model for a request for tickets in a group purchase."""

from __future__ import unicode_literals

from eisitirio import app
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
            single_parent=True,
            cascade="all, delete, delete-orphan",
            lazy='dynamic'
        )
    )

    requester_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=False
    )
    requester = DB.relationship(
        'User'
    )

    def __init__(self, ticket_type_slug, number_requested, purchase_group,
                 requester):
        self.ticket_type_slug = ticket_type_slug
        self.number_requested = number_requested
        self.purchase_group = purchase_group
        self.requester = requester

    def __repr__(self):
        return '<GroupPurchaseRequest({0}): {1} {2} tickets>'.format(
            self.object_id,
            self.number_requested,
            self.ticket_type_slug
        )

    @property
    def value(self):
        """Get the value of this request in pence."""
        return self.number_requested * self.ticket_type.price

    @property
    def value_pounds(self):
        """Get the value of this request as a string in pounds and pence."""
        value = '{0:03d}'.format(self.value)

        return value[:-2] + '.' + value[-2:]

    @property
    def ticket_type(self):
        """Get the ticket type object for this request."""
        return app.APP.config['TICKET_TYPES_BY_SLUG'][self.ticket_type_slug]

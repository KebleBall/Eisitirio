# coding: utf-8
"""Database model for representing postage for one or more tickets."""

from __future__ import unicode_literals

from eisitirio.database import db

DB = db.DB

POSTAGE_TICKET_LINK = DB.Table(
    'postage_ticket_link',
    DB.Model.metadata,
    DB.Column('postage_id',
              DB.Integer,
              DB.ForeignKey('postage.object_id')
             ),
    DB.Column('ticket_id',
              DB.Integer,
              DB.ForeignKey('ticket.object_id')
             )
)

class Postage(DB.Model):
    """Model for representing postage for one or more tickets."""
    __tablename__ = 'postage'

    paid = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=False
    )
    postage_type = DB.Column(
        DB.Unicode(50),
        nullable=False
    )
    price = DB.Column(
        DB.Integer(),
        nullable=False
    )
    address = DB.Column(
        DB.Unicode(200),
        nullable=True
    )

    tickets = DB.relationship(
        'Ticket',
        secondary=POSTAGE_TICKET_LINK,
        backref=DB.backref(
            'postage',
            lazy=False,
            uselist=False
        ),
        lazy='dynamic'
    )

    def __init__(self, postage_option, tickets, address=None):
        self.postage_type = postage_option.name
        self.price = postage_option.price
        self.address = address
        self.tickets = tickets

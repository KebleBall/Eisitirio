# coding: utf-8
"""Database model for representing an administration fee."""

from __future__ import unicode_literals

from eisitirio import app
from eisitirio.database import db

APP = app.APP
DB = db.DB

class AdminFee(DB.Model):
    """Model for representing an administration fee."""
    __tablename__ = 'admin_fee'

    amount = DB.Column(
        DB.Integer(),
        nullable=False
    )
    reason = DB.Column(
        DB.UnicodeText(),
        nullable=False
    )
    paid = DB.Column(
        DB.Boolean(),
        nullable=False,
        default=False
    )

    charged_to_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=False
    )
    charged_to = DB.relationship(
        'User',
        backref=DB.backref(
            'admin_fees_charged',
            lazy='dynamic'
        ),
        foreign_keys=[charged_to_id]
    )

    charged_by_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=False
    )
    charged_by = DB.relationship(
        'User',
        backref=DB.backref(
            'admin_fees_created',
            lazy='dynamic'
        ),
        foreign_keys=[charged_by_id]
    )

    def __init__(self, amount, reason, charged_to, charged_by):
        self.amount = amount
        self.reason = reason
        self.charged_to = charged_to
        self.charged_by = charged_by

    def __repr__(self):
        return '<AdminFee {0}: £{1}>'.format(self.object_id, self.amount_pounds)

    @property
    def amount_pounds(self):
        """Get the fee amount as a string of pounds and pence."""
        amount = '{0:03d}'.format(self.amount)
        return amount[:-2] + '.' + amount[-2:]

    def mark_as_paid(self):
        """Email the creator of this fee when it has been paid."""
        self.paid = True

        if "Ticket Upgrade:" in self.reason:
            possible_tickets = [int(x) for x in self.reason[16:].split(',')]
            for ticket in self.charged_to.active_tickets:
                if ticket.object_id in possible_tickets:
                    ticket.add_note('Upgrade')
        else:
            APP.email_manager.send_template(
                self.charged_by.email,
                'Administration fee paid.',
                'admin_fee_paid.email',
                fee=self
            )

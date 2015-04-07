# coding: utf-8
"""Database model for a discount voucher."""

from __future__ import unicode_literals

import datetime

from kebleball.database import db

DB = db.DB

class Voucher(DB.Model):
    """Model for a discount voucher."""
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    code = DB.Column(
        DB.Unicode(30),
        nullable=False
    )
    expires = DB.Column(
        DB.DateTime(),
        nullable=True
    )
    discount_type = DB.Column(
        DB.Enum(
            'Fixed Price',
            'Fixed Discount',
            'Percentage Discount'
        ),
        nullable=False
    )
    discount_value = DB.Column(
        DB.Integer(),
        nullable=False
    )
    applies_to = DB.Column(
        DB.Enum(
            'Ticket',
            'Transaction'
        ),
        nullable=False
    )
    single_use = DB.Column(
        DB.Boolean(),
        nullable=False
    )
    used = DB.Column(
        DB.Boolean(),
        default=False,
        nullable=True
    )

    used_by_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=True
    )
    used_by = DB.relationship(
        'User',
        backref=DB.backref(
            'vouchers_used',
            lazy='dynamic'
        )
    )

    def __init__(
            self,
            code,
            expires,
            discount_type,
            discount_value,
            applies_to,
            single_use
    ):
        if discount_type not in [
                'Fixed Price',
                'Fixed Discount',
                'Percentage Discount'
        ]:
            raise ValueError(
                '{0} is not a valid discount type'.format(discount_type)
            )

        if applies_to not in [
                'Ticket',
                'Transaction'
        ]:
            raise ValueError(
                '{0} is not a valid application'.format(applies_to)
            )

        self.code = code
        self.discount_type = discount_type
        self.discount_value = discount_value
        self.applies_to = applies_to
        self.single_use = single_use

        if isinstance(expires, datetime.timedelta):
            self.expires = datetime.datetime.utcnow() + expires
        else:
            self.expires = expires

    def __repr__(self):
        return '<Voucher: {0}/{1}>'.format(self.object_id, self.code)

    @staticmethod
    def get_by_id(object_id):
        """Get an Announcement object by its database ID."""
        voucher = Voucher.query.filter(
            Voucher.object_id == int(object_id)
        ).first()

        if not voucher:
            return None

        return voucher

    @staticmethod
    def get_by_code(code):
        """Get an Announcement object by a voucher code."""
        return Voucher.query().filter_by(Voucher.code == code).first()

    def apply(self, tickets, user):
        """Apply the voucher to a set of tickets.

        Checks if the voucher can be used, and applies its discount to the
        tickets.

        Args:
            tickets: (list(Ticket)) list of tickets to apply the voucher to
            user: (User) user who is using the voucher

        Returns:
            (bool, list(tickets), str/None) whether the voucher was applied, the
            mutated tickets, and an error message
        """
        if self.single_use and self.used:
            return (False, tickets, 'Voucher has already been used.')

        if (
                self.expires is not None and
                self.expires < datetime.datetime.utcnow()
        ):
            return (False, tickets, 'Voucher has expired.')

        self.used = True
        if self.single_use:
            if hasattr(user, 'object_id'):
                self.used_by_id = user.object_id
            else:
                self.used_by_id = user

        if self.applies_to == 'Ticket':
            tickets[0] = self.apply_to_ticket(tickets[0])
            return (True, tickets, None)
        else:
            return (True, [self.apply_to_ticket(t) for t in tickets], None)

    def apply_to_ticket(self, ticket):
        """Apply the voucher to a single ticket.

        Recalculates the price of the ticket, and notes on the ticket that a
        voucher was used

        Args:
            ticket: (Ticket) the ticket to apply the voucher to

        Returns:
            (ticket) the mutated ticket
        """
        if self.discount_type == 'Fixed Price':
            ticket.set_price(self.discount_value)
        elif self.discount_type == 'Fixed Discount':
            ticket.set_price(ticket.price - self.discount_value)
        else:
            ticket.set_price(ticket.price * (100 - self.discount_value) / 100)

        ticket.add_note(
            'Used voucher {0}/{1}'.format(self.object_id, self.code)
        )

        return ticket

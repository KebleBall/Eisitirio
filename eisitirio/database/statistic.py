# coding: utf-8
"""Database model for representing a statistic in a timeseries."""

from __future__ import unicode_literals

import collections
import datetime

from eisitirio.database import db

DB = db.DB

STATISTIC_GROUPS = collections.OrderedDict([
    ('college_users', 'Registered Users by College'),
    ('total_ticket_sales', 'Total Tickets by State'),
    ('guest_ticket_sales', 'Guest Tickets by State'),
    ('ticket_types', 'Active Tickets by Ticket Type'),
    ('payment_methods', 'Paid Tickets by Payment Method'),
    ('waiting', 'Waiting List'),
    ('dietary_requirements', 'Dietary Requirements'),
])

class Statistic(DB.Model):
    """Model for representing a statistic in a timeseries."""
    __tablename__ = 'statistic'

    timestamp = DB.Column(
        DB.DateTime,
        nullable=False
    )
    group = DB.Column(
        DB.Enum(*STATISTIC_GROUPS.keys()),
        nullable=False
    )
    statistic = DB.Column(
        DB.Unicode(25),
        nullable=False
    )
    value = DB.Column(
        DB.Integer(),
        nullable=False
    )

    def __init__(self, group, statistic, value):
        if group not in STATISTIC_GROUPS:
            raise ValueError(
                '{0} is not a valid statistic group'.format(group)
            )

        self.timestamp = datetime.datetime.utcnow()
        self.group = group
        self.statistic = statistic
        self.value = value

    def __repr__(self):
        return '<Statistic {0}/{1}/{2}: {3}>'.format(
            self.group,
            self.statistic,
            self.timestamp.strftime('%Y-%m-%d %H:%m (UTC)'),
            self.value
        )


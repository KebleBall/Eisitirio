# coding: utf-8
"""Database model for representing a statistic in a timeseries."""

from __future__ import unicode_literals

import datetime

from kebleball.database import db

DB = db.DB

class Statistic(DB.Model):
    """Model for representing a statistic in a timeseries."""
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    timestamp = DB.Column(
        DB.DateTime,
        nullable=False
    )
    group = DB.Column(
        DB.Enum(
            'Colleges',
            'Payments',
            'Sales'
        ),
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
        if group not in ['Colleges', 'Payments', 'Sales']:
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

    @staticmethod
    def get_by_id(object_id):
        """Get a Statistic object by its database ID."""
        statistic = Statistic.query.filter(
            Statistic.object_id == int(object_id)
        ).first()

        if not statistic:
            return None

        return statistic


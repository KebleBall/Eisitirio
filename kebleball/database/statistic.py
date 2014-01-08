# coding: utf-8
"""
statistic.py

Contains Statistic class
Used to store historical statistics for displaying graphs
"""

from kebleball.database import db
from datetime import datetime

class Statistic(db.Model):
    id = db.Column(
        db.Integer(),
        primary_key=True,
        nullable=False
    )
    timestamp = db.Column(
        db.DateTime,
        nullable=False
    )
    group = db.Column(
        db.Enum(
            'Colleges',
            'Payments',
            'Sales'
        ),
        nullable=False
    )
    statistic = db.Column(
        db.String(25),
        nullable=False
    )
    value = db.Column(
        db.Integer(),
        nullable=False
    )

    def __init__(self, group, statistic, value):
        if group not in ['Colleges','Payments','Sales']:
            raise ValueError(
                '{0} is not a valid statistic group'.format(group)
            )

        self.timestamp = datetime.utcnow()
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
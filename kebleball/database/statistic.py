# coding: utf-8
"""
statistic.py

Contains Statistic class
Used to store historical statistics for displaying graphs
"""

from kebleball.database import DB
from datetime import datetime

class Statistic(DB.Model):
    id = DB.Column(
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
        DB.String(25),
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

    @staticmethod
    def get_by_id(id):
        statistic = Statistic.query.filter(Statistic.id == int(id)).first()

        if not statistic:
            return None

        return statistic


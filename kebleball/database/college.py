# coding: utf-8
"""
college.py

Contains College class
Used to associate users with their colleges
"""

from kebleball.database import db

class College(db.Model):
    id = db.Column(
        db.Integer(),
        primary_key=True,
        nullable=False
    )
    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<College {0}: {1}>".format(self.id, self.name)
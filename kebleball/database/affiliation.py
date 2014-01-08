# coding: utf-8
"""
affiliation.py

Contains Affiliation class
Used to denote users' affiliations with their colleges
"""

from kebleball.database import db

class Affiliation(db.Model):
    id = db.Column(
        db.Integer(),
        primary_key=True,
        nullable=False
    )
    name = db.Column(
        db.String(25),
        nullable=False
    )

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Affiliation {0}: {1}>".format(self.id, self.name)
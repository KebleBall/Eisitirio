# coding: utf-8
"""Database model for representing a users affiliation to their college."""

from __future__ import unicode_literals

from eisitirio.database import db

DB = db.DB

class Affiliation(DB.Model):
    """Model for representing a users affiliation to their college."""
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    name = DB.Column(
        DB.Unicode(25),
        nullable=False
    )

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Affiliation {0}: {1}>'.format(self.object_id, self.name)

    @staticmethod
    def get_by_id(object_id):
        """Get an Affiliation object by its database ID."""
        affiliation = Affiliation.query.filter(
            Affiliation.object_id == int(object_id)
        ).first()

        if not affiliation:
            return None

        return affiliation

AFFILIATIONS = [
    Affiliation('Student'),
    Affiliation('Graduand'),
    Affiliation('Graduate/Alumnus'),
    Affiliation('Staff/Fellow'),
    Affiliation('Foreign Exchange Student'),
    Affiliation('Other'),
    Affiliation('None'),
]

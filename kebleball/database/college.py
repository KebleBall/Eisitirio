# coding: utf-8
"""Model for a user's college."""

from kebleball import database as db

DB = db.DB

class College(DB.Model):
    """Model for a user's college."""
    id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    name = DB.Column(
        DB.String(50),
        unique=True,
        nullable=False
    )

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<College {0}: {1}>".format(self.id, self.name)

    @staticmethod
    def get_by_id(id):
        """Get a college object by its ID."""
        college = College.query.filter(College.id == int(id)).first()

        if not college:
            return None

        return college


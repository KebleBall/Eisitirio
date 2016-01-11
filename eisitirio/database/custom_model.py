# coding: utf-8
"""Base table schema to reduce duplication."""

from __future__ import unicode_literals

from flask.ext import sqlalchemy as flask_sqlalchemy
import sqlalchemy

class CustomModel(flask_sqlalchemy.Model):
    """Base table schema to reduce duplication."""
    __tablename__ = None

    object_id = sqlalchemy.Column(
        sqlalchemy.Integer(),
        primary_key=True,
        nullable=False
    )

    def __repr__(self):
        return '<{0}({1})>'.format(self.__class__.__name__, self.object_id)

    @classmethod
    def get_by_id(cls, object_id):
        """Get an object by its database ID."""
        item = cls.query.filter(cls.object_id == int(object_id)).first()

        if not item:
            return None

        return item

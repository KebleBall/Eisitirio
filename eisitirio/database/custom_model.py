# coding: utf-8
"""Base table schema to reduce duplication.

Adds support for permission system, and adds default object_id column and
get_by_id method.
"""

from __future__ import unicode_literals

import functools

from flask.ext import sqlalchemy as flask_sqlalchemy
import sqlalchemy

from eisitirio.helpers import permissions

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
    def permission(cls, name=None):
        return permissions.permission(cls, name)

    @classmethod
    def possession(cls, name=None):
        return permissions.possession(cls, name)

    def can(self, name, *args, **kwargs):
        try:
            return permissions.PERMISSIONS[self.__class__][name](
                self,
                *args,
                **kwargs
            )
        except KeyError:
            raise AttributeError(
                'Permission {0} does not exist for model {1}'.format(
                    name,
                    self.__class__.__name__
                )
            )

    def has(self, name, *args, **kwargs):
        try:
            return permissions.POSSESSIONS[self.__class__][name](
                self,
                *args,
                **kwargs
            )
        except KeyError:
            raise AttributeError(
                'Possession {0} does not exist for model {1}'.format(
                    name,
                    self.__class__.__name__
                )
            )

    def __getattr__(self, name):
        if name.startswith('can_'):
            return functools.partial(self.can, name[4:])
        elif name.startswith('has_'):
            return functools.partial(self.has, name[4:])

        return super(CustomModel, self).__getattr__(name)

    @classmethod
    def get_by_id(cls, object_id):
        """Get an object by its database ID."""
        item = cls.query.filter(cls.object_id == int(object_id)).first()

        if not item:
            return None

        return item

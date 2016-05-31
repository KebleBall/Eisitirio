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

class CustomModelMeta(flask_sqlalchemy._BoundDeclarativeMeta): # pylint: disable=protected-access
    """Metaclass for the custom model to magically create get_by methods."""

    def __getattr__(cls, name): # this is a metaclass, pylint: disable=E0213
        if name.startswith('get_by_'):
            return functools.partial(cls.get_by, name[7:])

        return getattr(super(CustomModelMeta, cls), name)

    def get_by(cls, field_name, value): # this is a metaclass, pylint: disable=E0213
        """Get an object by the value of some field."""
        try:
            field = getattr(cls, field_name)
        except AttributeError:
            # Rewrite exception message to be nicer
            raise AttributeError(
                'Class \'{0}\' does not have a \'{1}\' field.'.format(
                    cls.__name__,
                    field_name
                )
            )

        if not isinstance(
                field,
                sqlalchemy.orm.attributes.InstrumentedAttribute
        ):
            raise AttributeError(
                'Class \'{0}\' does not have a \'{1}\' field.'.format(
                    cls.__name__,
                    field_name
                )
            )

        item = cls.query.filter(field == value).first()

        if not item:
            return None

        return item

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

    @property
    def identifier(self):
        return '{0:05d}'.format(self.object_id)

    @classmethod
    def permission(cls, name=None):
        """Define a permission function for this class.

        To be used as a decorator in the eisitirio.permissions module similar to
        the following:

            @models.Ticket.permission()
            def be_cancelled(ticket):
                # add logic here and return a boolean
        """
        return permissions.permission(cls, name)

    @classmethod
    def possession(cls, name=None):
        """Define a possession function for this class.

        To be used as a decorator in the eisitirio.permissions module similar to
        the following:

            @models.User.permission()
            def tickets(user):
                # add logic here and return a boolean
        """
        return permissions.possession(cls, name)

    def can(self, name, *args, **kwargs):
        """Check whether this object has permission to do something.

        Gets the permission function by |name|, and passes it this object and
        the args and kwargs.
        """
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
        """Check whether this object has a possession.

        Gets the possession function by |name|, and passes it this object and
        the args and kwargs.
        """
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
        """Neat way to access permission/possession functions.

        Allows using can_be_cancelled in place of can('be_cancelled') and
        has_tickets in place of has('tickets').
        """
        if name.startswith('can_'):
            return functools.partial(self.can, name[4:])
        elif name.startswith('has_'):
            return functools.partial(self.has, name[4:])

        return getattr(super(CustomModel, self), name)

    @classmethod
    def get_by_id(cls, object_id):
        """Get an object by its database ID."""
        item = cls.query.filter(cls.object_id == int(object_id)).first()

        if not item:
            return None

        return item

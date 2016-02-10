# coding: utf-8
"""Database model for representing a guest's dietary requirements."""

from __future__ import unicode_literals

from eisitirio.database import db

DB = db.DB

class DietaryRequirements(DB.Model):
    """Model for representing a users affiliation to their college."""
    __tablename__ = 'dietary_requirements'

    user_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('user.object_id'),
        nullable=False
    )
    user = DB.relationship(
        'User',
        backref=DB.backref(
            'dietary_requirements',
            uselist=False
        )
    )

    pescetarian = DB.Column(
        DB.Boolean,
        default=False,
        nullable=False
    )
    vegetarian = DB.Column(
        DB.Boolean,
        default=False,
        nullable=False
    )
    vegan = DB.Column(
        DB.Boolean,
        default=False,
        nullable=False
    )
    gluten_free = DB.Column(
        DB.Boolean,
        default=False,
        nullable=False
    )
    nut_free = DB.Column(
        DB.Boolean,
        default=False,
        nullable=False
    )
    dairy_free = DB.Column(
        DB.Boolean,
        default=False,
        nullable=False
    )
    egg_free = DB.Column(
        DB.Boolean,
        default=False,
        nullable=False
    )
    seafood_free = DB.Column(
        DB.Boolean,
        default=False,
        nullable=False
    )

    other = DB.Column(
        DB.String(200),
        nullable=True
    )

    def __init__(self, user):
        self.user = user

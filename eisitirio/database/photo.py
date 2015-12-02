# coding: utf-8
"""Database model for representing a users affiliation to their college."""

from __future__ import unicode_literals

from eisitirio.database import db

DB = db.DB

class Photo(DB.Model):
    """Model for representing a photo stored on S3."""
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    filename = DB.Column(
        DB.Unicode(50),
        nullable=False
    )
    full_url = DB.Column(
        DB.Unicode(250),
        nullable=False
    )
    thumb_url = DB.Column(
        DB.Unicode(250),
        nullable=False
    )

    def __init__(self, filename, full_url, thumb_url):
        self.filename = filename
        self.full_url = full_url
        self.thumb_url = thumb_url

    def __repr__(self):
        return '<Photo {0}: {1}>'.format(self.object_id, self.filename)

    @staticmethod
    def get_by_id(object_id):
        """Get an Photo object by its database ID."""
        photo = Photo.query.filter(
            Photo.object_id == int(object_id)
        ).first()

        if not photo:
            return None

        return photo

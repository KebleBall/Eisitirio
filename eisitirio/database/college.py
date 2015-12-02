# coding: utf-8
"""Database model for a user's college."""

from __future__ import unicode_literals

from eisitirio.database import db

DB = db.DB

class College(DB.Model):
    """Model for a user's college."""
    object_id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    name = DB.Column(
        DB.Unicode(50),
        unique=True,
        nullable=False
    )

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<College {0}: {1}>'.format(self.object_id, self.name)

    @staticmethod
    def get_by_id(object_id):
        """Get a college object by its ID."""
        college = College.query.filter(
            College.object_id == int(object_id)
        ).first()

        if not college:
            return None

        return college

COLLEGES = [
    College('All Souls'),
    College('Balliol'),
    College('Blackfriars'),
    College('Brasenose'),
    College('Campion Hall'),
    College('Christ Church'),
    College('Corpus Christi'),
    College('Exeter'),
    College('Green Templeton'),
    College('Harris Manchester'),
    College('Hertford'),
    College('Jesus'),
    College('Keble'),
    College('Kellogg'),
    College('Lady Margaret Hall'),
    College('Linacre'),
    College('Lincoln'),
    College('Magdelen'),
    College('Mansfield'),
    College('Merton'),
    College('New'),
    College('Nuffield'),
    College('Oriel'),
    College('Pembroke'),
    College('Queen\'s'),
    College('Regent\'s Park'),
    College('Somerville'),
    College('St Anne\'s'),
    College('St Antony\'s'),
    College('St Benet\'s Hall'),
    College('St Catherine\'s'),
    College('St Cross'),
    College('St Edmund Hall'),
    College('St Hilda\'s'),
    College('St Hugh\'s'),
    College('St John\'s'),
    College('St Peter\'s'),
    College('St Stephen\'s House'),
    College('Trinity'),
    College('University'),
    College('Wadham'),
    College('Wolfson'),
    College('Worcester'),
    College('Wycliffe Hall'),
    College('Other'),
    College('None'),
]

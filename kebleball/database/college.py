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

    @staticmethod
    def get_by_id(id):
        college = College.query.filter(College.id==int(id)).first()

        if not college:
            return None

        return college

COLLEGES = [
    College("All Souls"),
    College("Balliol"),
    College("Blackfriars"),
    College("Brasenose"),
    College("Campion Hall"),
    College("Christ Church"),
    College("Corpus Christi"),
    College("Exeter"),
    College("Green Templeton"),
    College("Harris Manchester"),
    College("Hertford"),
    College("Jesus"),
    College("Keble"),
    College("Kellogg"),
    College("Lady Margaret Hall"),
    College("Linacre"),
    College("Lincoln"),
    College("Magdelen"),
    College("Mansfield"),
    College("Merton"),
    College("New"),
    College("Nuffield"),
    College("Oriel"),
    College("Pembroke"),
    College("Queen's"),
    College("Regent's Park"),
    College("Somerville"),
    College("St Anne's"),
    College("St Antony's"),
    College("St Benet's Hall"),
    College("St Catherine's"),
    College("St Cross"),
    College("St Edmund Hall"),
    College("St Hilda's"),
    College("St Hugh's"),
    College("St John's"),
    College("St Peter's"),
    College("St Stephen's House"),
    College("Trinity"),
    College("University"),
    College("Wadham"),
    College("Wolfson"),
    College("Worcester"),
    College("Wycliffe Hall"),
    College("Other"),
    College("None"),
]

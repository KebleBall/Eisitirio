# coding: utf-8
"""Script to prefill the database with colleges and affiliations."""

from __future__ import unicode_literals

from flask.ext import script

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import static

class PrefillCommand(script.Command):
    """Flask-Script command for prefilling the database."""

    help = 'Prefill database with colleges and affiliations'

    @staticmethod
    def run():
        """Prefill the database."""
        with app.APP.app_context():
            db.DB.session.add_all(static.COLLEGES)
            db.DB.session.add_all(static.AFFILIATIONS)
            db.DB.session.commit()

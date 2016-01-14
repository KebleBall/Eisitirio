#!/usr/bin/env python2
# coding: utf-8
"""Script to prefill the database with colleges and affiliations."""

from flask.ext import script

from eisitirio.database import db
from eisitirio.database import static

class PrefillCommand(script.Command):
    """Flask-Script command for prefilling the database."""

    help = 'Prefill database with colleges and affiliations'

    @staticmethod
    def run():
        """Prefill the database."""

        db.DB.session.add_all(static.COLLEGES)
        db.DB.session.add_all(static.AFFILIATIONS)
        db.DB.session.commit()

# coding: utf-8
"""Script to create claim codes for tickets."""

from __future__ import unicode_literals

import string

from flask.ext import script

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import util

class CreateClaimCodesCommand(script.Command):
    """Flask-Script command for creating ticket claim codes."""

    help = 'Create claim codes for tickets'

    @staticmethod
    def run():
        """Create the claim codes."""
        with app.APP.app_context():
            tickets = models.Ticket.query.filter(
                models.Ticket.claim_code == None # pylint: disable=singleton-comparison
            ).all()

            for ticket in tickets:
                ticket.claim_code = '-'.join(
                    util.generate_key(5, string.digits)
                    for _ in xrange(3)
                ).decode('utf-8')

                db.DB.session.commit()

# coding: utf-8
"""Script to migrate postage entries to have owners."""

from __future__ import unicode_literals

from flask.ext import script

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

class MigratePostageCommand(script.Command):
    """Flask-Script command for migrating postage entries."""

    help = 'Migrate postage entries to have owners.'

    @staticmethod
    def run():
        """Run the migration."""
        with app.APP.app_context():
            postage_entries = models.Postage.query.filter(
                models.Postage.owner == None # pylint: disable=singleton-comparison
            ).all()

            for postage in postage_entries:
                try:
                    transaction_item = postage.transaction_items[0]
                except IndexError:
                    # No transaction items
                    continue

                postage.owner = transaction_item.transaction.user

                db.DB.session.commit()

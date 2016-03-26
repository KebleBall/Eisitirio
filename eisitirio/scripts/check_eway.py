# coding: utf-8
"""Script to check if eWay payments have been completed."""

from __future__ import unicode_literals

from flask.ext import script

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.logic import eway_logic

APP = app.APP
DB = db.DB

class CheckEwayCommand(script.Command):
    """Command for checking if eWay payments have been completed."""

    help = 'Check if eWay payments have been completed.'

    @staticmethod
    def run():
        """Perform the checking."""
        with app.APP.app_context():
            for transaction in models.CardTransaction.query.filter(
                    models.CardTransaction.paid == False # pylint: disable=singleton-comparison
            ).all():
                if transaction.eway_transaction is None:
                    continue

                if transaction.eway_transaction.result_code is not None:
                    continue

                eway_logic.process_payment(transaction, False, True)

                print "#{0:05d}: {1}".format(
                    transaction.object_id,
                    transaction.eway_transaction.success
                )

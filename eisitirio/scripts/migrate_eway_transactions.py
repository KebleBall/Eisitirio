#!/usr/bin/env python2
# coding: utf-8
"""Script to migrate to the new Eway Transaction model."""

from flask.ext import script

from eisitirio.database import db
from eisitirio.database import models

DB = db.DB

class MigrateEwayTransactionsCommand(script.Command):
    """Flask-Script command for migrating eWay transactions."""

    help = 'Migrate to the new Eway Transaction model'

    @staticmethod
    def run():
        """Perform the migration."""

        for transaction in models.OldCardTransaction.query:
            if transaction.access_code:
                eway = models.EwayTransaction(transaction.access_code,
                                              transaction.value)

                eway.completed = transaction.completed
                eway.result_code = transaction.result_code
                eway.eway_id = transaction.eway_id
                eway.refunded = transaction.refunded

                DB.session.add(eway)
            else:
                eway = None

            new_transaction = models.CardTransaction(transaction.user, eway)

            new_transaction.paid = transaction.paid
            new_transaction.created = transaction.created

            DB.session.add(new_transaction)

            for item in transaction.items:
                item.transaction = new_transaction

            for event in transaction.events:
                event.transaction = new_transaction

            DB.session.delete(transaction)

            DB.session.commit()

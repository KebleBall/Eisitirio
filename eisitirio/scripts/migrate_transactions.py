#!/usr/bin/env python2
# coding: utf-8
"""Script to migrate Transactions to the new polymorphic style."""

from flask.ext import script

from eisitirio.database import db
from eisitirio.database import models

DB = db.DB

class MigrateTransactionsCommand(script.Command):
    """Flask-Script command for migrating transactions."""

    help = 'Migrate Transactions to the polymorphic style.'

    @staticmethod
    def run():
        """Perform the migration."""
        for transaction in models.OldTransaction.query.all():
            if transaction.value == 0:
                new_transaction = models.Transaction(transaction.user, 'Free')
            elif transaction.payment_method == 'Battels':
                new_transaction = models.BattelsTransaction(transaction.user)

                new_transaction.battels_term = transaction.battels_term
            elif transaction.payment_method == 'Card':
                new_transaction = models.CardTransaction(transaction.user)

                old_card_transaction = transaction.card_transaction

                new_transaction.completed = old_card_transaction.completed
                new_transaction.access_code = old_card_transaction.access_code
                new_transaction.result_code = old_card_transaction.result_code
                new_transaction.eway_id = old_card_transaction.eway_id
                new_transaction.refunded = old_card_transaction.refunded

                for event in transaction.card_transaction.events:
                    event.transaction = new_transaction
                    event.card_transaction = None
                    event.card_transaction_id = None

                DB.session.delete(transaction.card_transaction)
            else:
                new_transaction = models.Transaction(transaction.user, 'Dummy')

            new_transaction.paid = transaction.paid
            new_transaction.created = transaction.created

            for item in transaction.items:
                item.transaction = new_transaction
                item.old_transaction = None
                item.old_transaction_id = None

            DB.session.delete(transaction)

            DB.session.commit()

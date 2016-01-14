#!/usr/bin/env python2
# coding: utf-8
"""Script to migrate transaction items to the new polymorphic style."""

import collections

from flask.ext import script

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

APP = app.APP
DB = db.DB

DummyPostageOption = collections.namedtuple('DummyPostageOption',
                                            ['name', 'price'])

class MigrateTransactionItemsCommand(script.Command):
    """Flask-Script command for migrating transaction items."""

    help = 'Migrate transaction items'

    @staticmethod
    def run():
        """Perform the migration."""

        for transaction in models.Transaction.query.all():
            for item in transaction.old_items:
                if item.item_type == 'Ticket':
                    DB.session.add(models.TicketTransactionItem(
                        transaction, item.ticket
                    ))
                elif item.item_type == 'Postage':
                    if (
                            item._description ==
                            APP.config['NO_POSTAGE_OPTION'].name
                    ):
                        continue

                    postage = models.Postage(
                        DummyPostageOption(item._description, item._value),
                        transaction.tickets,
                        transaction.address
                    )

                    postage.paid = transaction.paid

                    DB.session.add(postage)

                    DB.session.add(models.PostageTransactionItem(
                        transaction,
                        postage
                    ))
                else:
                    DB.session.rollback()

                    raise ValueError("Unexpected item type")

                DB.session.delete(item)

            DB.session.commit()

# coding: utf-8
"""Script to fix postage entries for graduands."""

from __future__ import unicode_literals

import flask_script as script
# from flask.ext import script

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

APP = app.APP
DB = db.DB

class FixGraduandPostageCommand(script.Command):
    """Flask-Script command for fixing postage entries for graduands."""

    help = 'Fix postage entries for graduands'

    @staticmethod
    def run():
        """Run the fixing."""
        with app.APP.app_context():
            graduand_query = models.User.query.join(
                models.User.affiliation
            ).filter(
                models.Affiliation.name == 'Graduand'
            )

            for user in graduand_query:
                if not needs_fixing(user):
                    continue

                entry = get_graduand_postage_entry(user)

                for ticket in user.tickets:
                    if ticket.postage is None:
                        entry.tickets.append(ticket)
                    else:
                        if ticket.postage == entry:
                            continue
                        elif (
                                not ticket.postage.paid or
                                ticket.postage.cancelled or
                                (
                                    ticket.postage.postage_type ==
                                    APP.config['GRADUAND_POSTAGE_OPTION'].name
                                )
                        ):
                            ticket.postage.cancelled = True
                            ticket.postage.tickets.remove(ticket)

                            entry.tickets.append(ticket)

                DB.session.commit()

def needs_fixing(user):
    """Check if the user's postage entries need fixing."""
    return any(
        ticket.postage is None or
        (
            ticket.postage.postage_type ==
            APP.config['GRADUAND_POSTAGE_OPTION'].name
        )
        for ticket in user.tickets
    )

def get_graduand_postage_entry(user):
    """Get the first graduand postage entry for the user, or create one."""
    for entry in user.postage_entries:
        if entry.postage_type == APP.config['GRADUAND_POSTAGE_OPTION'].name:
            return entry

    entry = models.Postage(
        user,
        APP.config['GRADUAND_POSTAGE_OPTION'],
        [],
        None
    )

    DB.session.add(entry)

    DB.session.add(models.PostageTransactionItem(get_transaction(user), entry))

    return entry

def get_transaction(user):
    """Get a transaction to attach a postage entry to, or create one."""
    for transaction in user.transactions:
        if transaction.postage is None:
            return transaction

    transaction = models.DummyTransaction(user)

    db.DB.session.add(transaction)

    return transaction

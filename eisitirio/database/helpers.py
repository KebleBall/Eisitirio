# coding: utf-8
"""Helper to prepare the database for use."""

from eisitirio.database import db
from eisitirio.database import models
from eisitirio.database import static

def initialise_db(prefill=True, clear=False):
    """Prepare the database for use.

    Creates all the database tables, optionally clears existing data and loads
    constant data. Intended to be run interactively.

    Args:
        prefill: (bool) whether to add constant data (colleges/affiliations)
        clear: (bool) whether to remove all existing data from tables
    """
    db.DB.create_all()

    if clear:
        prompt = raw_input(
            'Are you sure you wish to clear the entire database? '
        )

        if prompt.lower() in ['yes', 'y']:
            models.Affiliation.query.delete()
            models.Announcement.query.delete()
            models.Battels.query.delete()
            models.CardTransaction.query.delete()
            models.College.query.delete()
            models.Log.query.delete()
            models.Photo.query.delete()
            models.Statistic.query.delete()
            models.Ticket.query.delete()
            models.Transaction.query.delete()
            models.TransactionItem.query.delete()
            models.User.query.delete()
            models.Voucher.query.delete()
            models.Waiting.query.delete()

    if prefill:
        db.DB.session.add_all(static.COLLEGES)
        db.DB.session.add_all(static.AFFILIATIONS)
        db.DB.session.commit()

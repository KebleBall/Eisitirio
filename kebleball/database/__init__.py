# coding: utf-8
"""Manages access to the database.

Submodules define the database connection object and the various data modules.
Defined here is a helper for initialising the database
"""

from kebleball.database import affiliation
from kebleball.database import announcement
from kebleball.database import battels
from kebleball.database import card_transaction
from kebleball.database import college
from kebleball.database import db
from kebleball.database import log
from kebleball.database import statistic
from kebleball.database import ticket
from kebleball.database import user
from kebleball.database import voucher
from kebleball.database import waiting

DB = db.DB

def initialise_db(prefill=True, clear=False):
    DB.create_all()

    if clear:
        prompt = input("Are you sure you wish to clear the entire database? ")
        if prompt.lower() in ["yes", "y"]:
            affiliation.Affiliation.query.delete()
            announcement.Announcement.query.delete()
            battels.Battels.query.delete()
            card_transaction.CardTransaction.query.delete()
            college.College.query.delete()
            log.Log.query.delete()
            statistic.Statistic.query.delete()
            ticket.Ticket.query.delete()
            user.User.query.delete()
            voucher.Voucher.query.delete()
            waiting.Waiting.query.delete()

    if prefill:
        DB.session.add_all(college.COLLEGES)
        DB.session.add_all(affiliation.AFFILIATIONS)
        DB.session.commit()

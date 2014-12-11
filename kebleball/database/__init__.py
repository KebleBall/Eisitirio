# coding: utf-8
"""Manages access to the database.

Initialises the SQLAlchemy connection, and provides a passthrough to the various
database models.
"""

from flask.ext import sqlalchemy as flask_sqlalchemy
from kebleball import app

DB = flask_sqlalchemy.SQLAlchemy(app.APP)

from kebleball.database import affiliation
from kebleball.database import announcement
from kebleball.database import battels
from kebleball.database import card_transaction
from kebleball.database import college
from kebleball.database import log
from kebleball.database import statistic
from kebleball.database import ticket
from kebleball.database import user
from kebleball.database import voucher
from kebleball.database import waiting

Affiliation = affiliation.Affiliation
Announcement = announcement.Announcement
Battels = battels.Battels
CardTransaction = card_transaction.CardTransaction
College = college.College
Log = log.Log
Statistic = statistic.Statistic
Ticket = ticket.Ticket
User = user.User
Voucher = voucher.Voucher
Waiting = waiting.Waiting

def initialise_db(prefill=True, clear=False):
    db.create_all()

    if clear:
        prompt = input("Are you sure you wish to clear the entire database? ")
        if prompt.lower() in ["yes", "y"]:
            Affiliation.query.delete()
            Announcement.query.delete()
            Battels.query.delete()
            CardTransaction.query.delete()
            College.query.delete()
            Log.query.delete()
            Statistic.query.delete()
            Ticket.query.delete()
            User.query.delete()
            Voucher.query.delete()
            Waiting.query.delete()

    if prefill:
        db.session.add_all(college.COLLEGES)
        db.session.add_all(affiliation.AFFILIATIONS)
        db.session.commit()

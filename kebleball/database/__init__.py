# coding: utf-8
"""
database

Manages access to database
"""

__all__ = ['db', 'Affiliation', 'Announcement', 'Battels', 'CardTransaction', 'College', 'Log', 'Statistic', 'Ticket', 'User', 'Voucher', 'Waiting']

from flask.ext.sqlalchemy import SQLAlchemy
from kebleball import app

db = SQLAlchemy(app)

from .affiliation import Affiliation
from .announcement import Announcement
from .battels import Battels
from .card_transaction import CardTransaction
from .college import College
from .log import Log
from .statistic import Statistic
from .ticket import Ticket
from .user import User
from .voucher import Voucher
from .waiting import Waiting

from .college import COLLEGES
from .affiliation import AFFILIATIONS

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
        db.session.add_all(COLLEGES)
        db.session.add_all(AFFILIATIONS)
        db.session.commit()

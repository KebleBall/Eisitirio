"""
database

Manages access to database
"""

__all__ = ['db', 'Affiliation', 'Announcement', 'Battels_auto', 'Battels_manual',
           'College', 'Log', 'Statistic', 'Ticket', 'User', 'Voucher', 'Waiting']

from flask.ext.sqlalchemy import SQLAlchemy
from kebleball import app

db = SQLAlchemy(app)

from affiliation import Affiliation
from announcement import Announcement
# from battels_auto import Battels_auto
# from battels_manual import Battels_manual
from college import College
# from log import Log
# from statistic import Statistic
# from ticket import Ticket
from user import User
# from voucher import Voucher
# from waiting import Waiting
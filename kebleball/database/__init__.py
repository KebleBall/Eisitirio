"""
database

Manages access to database
"""

from flask.ext.sqlalchemy import SQLAlchemy
from kebleball import app

db = SQLAlchemy(app)

from affiliation import Affiliation
from announcement import Announcement
from battels import Battels
from college import College
from log import Log
# from statistic import Statistic
# from ticket import Ticket
from user import User
# from voucher import Voucher
# from waiting import Waiting
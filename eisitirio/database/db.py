# coding: utf-8
"""Creates the SQLAlchemy connection object"""

from flask.ext import sqlalchemy

from eisitirio import app

DB = sqlalchemy.SQLAlchemy(app.APP)

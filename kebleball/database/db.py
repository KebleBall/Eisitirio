# coding: utf-8
"""Creates the SQLAlchemy connection object"""

from flask.ext import sqlalchemy

from kebleball import app

DB = sqlalchemy.SQLAlchemy(app.APP)

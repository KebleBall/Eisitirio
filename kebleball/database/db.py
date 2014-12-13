# coding: utf-8
"""Creates the SQLAlchemy connection object"""

from flask.ext import sqlalchemy as flask_sqlalchemy
from kebleball import app

DB = flask_sqlalchemy.SQLAlchemy(app.APP)

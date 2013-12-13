"""
database

Manages access to database
"""

from flask.ext.sqlalchemy import SQLAlchemy
from kebleball import app

db = SQLAlchemy(app)
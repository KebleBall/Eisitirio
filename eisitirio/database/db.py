# coding: utf-8
"""Creates the SQLAlchemy connection object"""

from flask.ext import sqlalchemy as flask_sqlalchemy
from sqlalchemy.dialects import mysql
from sqlalchemy.ext import declarative
import sqlalchemy

from eisitirio import app
from eisitirio.database import custom_model

DB = flask_sqlalchemy.SQLAlchemy(app.APP)

# Awkward hack to use a custom model class. Flask-SQLAlchemy 3.0 (in beta as of
# 2016-01-11) has a model_class parameter to the above constructor, which should
# be used once v3.0 is released as stable.
DB.Model = declarative.declarative_base(
    cls=custom_model.CustomModel,
    name='Model',
    metadata=None,
    metaclass=custom_model.CustomModelMeta
)
DB.Model.query = flask_sqlalchemy._QueryProperty(DB) # pylint: disable=protected-access

@sqlalchemy.event.listens_for(sqlalchemy.Table, "column_reflect")
def column_reflect(_, unused, column_info):
    if isinstance(column_info['type'], mysql.TINYINT):
        column_info['type'] = sqlalchemy.Boolean()

    if isinstance(column_info['type'], mysql.MEDIUMTEXT):
        column_info['type'] = sqlalchemy.UnicodeText(length=65536)

    if isinstance(column_info['type'], mysql.TEXT):
        column_info['type'] = sqlalchemy.UnicodeText(length=256)

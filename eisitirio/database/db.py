# coding: utf-8
"""Creates the SQLAlchemy connection object"""

from flask.ext import sqlalchemy
from sqlalchemy.ext import declarative

from eisitirio import app
from eisitirio.database import custom_model

DB = sqlalchemy.SQLAlchemy(app.APP)

# Awkward hack to use a custom model class. Flask-SQLAlchemy 3.0 (in beta as of
# 2016-01-11) has a model_class parameter to the above constructor, which should
# be used once v3.0 is released as stable.
DB.Model = declarative.declarative_base(
    cls=custom_model.CustomModel,
    name='Model',
    metadata=None,
    metaclass=custom_model.CustomModelMeta
)
DB.Model.query = sqlalchemy._QueryProperty(DB) # pylint: disable=protected-access

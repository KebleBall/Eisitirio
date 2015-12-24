#!/usr/bin/env python2
# coding: utf-8
"""Script to invoke Flask-Migrate."""

from __future__ import unicode_literals

from flask.ext import script
from flask.ext import migrate

from kebleball import app
from kebleball import system
from kebleball.database import db
from kebleball.database import models

if __name__ == '__main__':
    app.APP.config.from_pyfile('config/development.py')

    MIGRATE = migrate.Migrate(app.APP, db.DB)

    MANAGER = script.Manager(app.APP)
    MANAGER.add_command('db', migrate.MigrateCommand)

    MANAGER.run()

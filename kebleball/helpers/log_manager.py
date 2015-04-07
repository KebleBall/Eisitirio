# coding: utf-8
"""Helper class to log events, both for users actions and for system errors."""

from __future__ import unicode_literals

import logging

from flask.ext import login
import flask

from kebleball.database import db
from kebleball.database import models

DB = db.DB

class LogManager(object):
    """Helper to log events, both for users actions and for system errors.

    Provides passthroughs to various loggers written to disk, plus a separate
    logging method for logging user actions to the database.
    """
    def __init__(self, app):
        app.log_manager = self

        logging.basicConfig(
            level=app.config['LOG_LEVEL'],
            format=(
                '[%(name)s/%(levelname)s] '
                '%(asctime)s - '
                '%(message)s'
            ),
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        self.admin = logging.getLogger('admin')
        self.ajax = logging.getLogger('ajax')
        self.dashboard = logging.getLogger('dashboard')
        self.database = logging.getLogger('database')
        self.email = logging.getLogger('email')
        self.front = logging.getLogger('front')
        self.main = logging.getLogger('main')
        self.purchase = logging.getLogger('purchase')
        self.resale = logging.getLogger('purchase')

    def init_app(self, app):
        app.logger = self

    def log(self, module, level, message):
        getattr(getattr(self, module), level)(message)

    def __getattr__(self, name):
        components = name.split('_')

        if len(components) == 2:
            if components[1] in [
                    'admin',
                    'ajax',
                    'dashboard',
                    'database',
                    'email',
                    'front',
                    'main',
                    'purchase',
                    'resale',
            ]:
                return lambda level, message: self.log(
                    components[1],
                    level,
                    message
                )

        raise AttributeError(
            'LogManager instance has no attribute "{0}"'.format(name)
        )

    def log_event(self, message, tickets=None, user=None, transaction=None):  # pylint: disable=no-self-use
        """Log a user action to the database.

        Creates a log entry in the database which can be found through the admin
        interface.

        Args:
            message: (str) The message to be logged
            tickets: (list(models.Ticket) or None) tickets the action affected
            user: (models.User or None) user this action affected
            transaction: (models.CardTransaction or None) transaction this
                action affected
        """
        if 'actor_id' in flask.session:
            actor = flask.session['actor_id']
        elif not login.current_user.is_anonymous():
            actor = login.current_user
        else:
            actor = None

        if isinstance(user, login.AnonymousUserMixin):
            user = None

        if tickets is None:
            tickets = []

        entry = models.Log(
            flask.request.remote_addr,
            message,
            actor,
            user,
            tickets,
            transaction
        )

        DB.session.add(entry)
        DB.session.commit()

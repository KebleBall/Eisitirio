# coding: utf-8
"""Helper class to log events, both for users actions and for system errors."""

from __future__ import unicode_literals

import logging

from flask.ext import login
import flask

from eisitirio.database import db
from eisitirio.database import models

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

    def init_app(self, app):
        """Add this instance to the app."""
        app.logger = self

    def log(self, module, level, message):
        """Log a message for a given module."""
        getattr(getattr(self, module), level)(message)

    def __getattr__(self, name):
        components = name.split('_')

        if len(components) == 2 and components[1] in [
                'admin',
                'ajax',
                'dashboard',
                'database',
                'email',
                'front',
                'main',
                'purchase',
        ]:
            return lambda level, message: self.log(
                components[1],
                level,
                message
            )

        raise AttributeError(
            'LogManager instance has no attribute "{0}"'.format(name)
        )

    @staticmethod
    def log_event(message, tickets=None, user=None, transaction=None,
                  purchase_group=None, admin_fee=None, commit=True,
                  in_app=True):
        """Log a user action to the database.

        Creates a log entry in the database which can be found through the admin
        interface.

        Args:
            message: (str) The message to be logged
            tickets: (list(models.Ticket) or None) tickets the action affected
            user: (models.User or None) user this action affected
            transaction: (models.Transaction or None) transaction this action
                affected
        """
        actor = None

        if in_app:
            if 'actor_id' in flask.session:
                actor = models.User.get_by_id(flask.session['actor_id'])
            elif not login.current_user.is_anonymous:
                actor = login.current_user

            ip_address = flask.request.remote_addr.decode()
        else:
            ip_address = 'interactive'

        if isinstance(user, login.AnonymousUserMixin):
            user = None

        if tickets is None:
            tickets = []

        entry = models.Log(
            ip_address,
            message,
            actor,
            user,
            tickets,
            transaction,
            purchase_group,
            admin_fee
        )

        DB.session.add(entry)

        if commit:
            DB.session.commit()

# coding: utf-8
"""
log_manager.py

Contains Logger class
Used to log events, both for users and for system errors
"""

import logging
from kebleball.database import db
from kebleball.database.log import Log
from flask import session, current_app
from flask.ext.login import current_user, request

class LogManager(object):
    def __init__(self, app):
        logging.basicConfig(
            level=app.config['LOG_LEVEL'],
            format=(
                "[%(name)s/%(levelname)s] "
                "%(asctime)s - "
                "%(message)s"
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

        self.session = session

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
                    "Logger instance has no attribute '{0}'".format(name)
                )

    def log_event(self, message, tickets=[], user=None, transaction=None):
        if 'actor_id' in self.session:
            actor = self.session['actor_id']
        elif not current_user.is_anonymous():
            actor = current_user
        else:
            actor = None

        entry = Log(
            request.remote_addr,
            message,
            actor,
            user,
            tickets,
            transaction
        )

        session = db.create_scoped_session()

        session.merge(entry)
        session.commit()
        session.close()
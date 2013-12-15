"""
logger.py

Contains Logger class
Used to log events, both for users and for system errors
"""

import logging
from kebleball.database import db
from kebleball.database.log import Log
from flask import session
from flask.ext.login import current_user, request

class Logger():
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
        self.front = logging.getLogger('front')
        self.main = logging.getLogger('main')
        self.purchase = logging.getLogger('purchase')
        self.resale = logging.getLogger('purchase')

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

    def log_event(self, message, ticket=None):
        if 'actor_id' in session:
            actor = session['actor_id']
        else:
            actor = current_user

        entry = Log(
            request.remote_addr,
            message,
            actor,
            current_user,
            ticket
        )

        session = db.create_scoped_session()

        session.add(entry)
        session.commit()
        session.close()
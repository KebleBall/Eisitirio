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
        self.loggers = {}

        try:
            handler = logging.FileHandler(app.config['LOG_LOCATION'])
        except KeyError:
            # If LOG_LOCATION is not set, we log to console
            handler = logging.StreamHandler()

        formatter = logging.Formatter(
            fmt = (
                "[%(name)s/%(levelname)s] "
                "%(asctime)s - "
                "%(message)s"
            ),
            datefmt = '%Y-%m-%d %H:%M:%S'
        )

        handler.setFormatter(formatter)

        self.loggers['admin'] = logging.getLogger('admin')
        self.loggers['ajax'] = logging.getLogger('ajax')
        self.loggers['dashboard'] = logging.getLogger('dashboard')
        self.loggers['database'] = logging.getLogger('database')
        self.loggers['front'] = logging.getLogger('front')
        self.loggers['main'] = logging.getLogger('main')
        self.loggers['purchase'] = logging.getLogger('purchase')
        self.loggers['resale'] = logging.getLogger('purchase')

        for key in self.loggers.iterkeys():
            self.loggers[key].setLevel(app.config['LOG_LEVEL'])
            self.loggers[key].addHandler(handler)

    def log(self, module, level, message):
        getattr(self.loggers[module], level)(message)

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
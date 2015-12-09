#!/usr/bin/env python2
# coding: utf-8
"""Script to update matching from users to Battels accounts."""

import os

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

APP = app.APP
DB = db.DB

def main():
    """Load the appropriate config and perform the matching."""
    if 'EISITIRIO_ENV' in os.environ:
        if os.environ['EISITIRIO_ENV'] == 'DEVELOPMENT':
            APP.config.from_pyfile('config/development.py')
        elif os.environ['EISITIRIO_ENV'] == 'STAGING':
            APP.config.from_pyfile('config/staging.py')
        elif os.environ['EISITIRIO_ENV'] == 'PRODUCTION':
            APP.config.from_pyfile('config/production.py')

    for user in models.User.query.all():
        if user.battels is not None:
            continue

        battels = models.Battels.query.filter(
            models.Battels.email == user.email
        ).first()

        if battels is not None:
            user.battels = battels
            DB.session.commit()

if __name__ == '__main__':
    main()

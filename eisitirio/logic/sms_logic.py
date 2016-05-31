# coding: utf-8
"""Logic for dealing with SMS messages."""

from __future__ import unicode_literals

import logging
import random

from eisitirio import app
from eisitirio.database import db

APP = app.APP
DB = db.DB

LOG = logging.getLogger(__name__)

def maybe_send_verification_code(user):
    """Send a verification code to the user's phone if necessary."""
    if not APP.config['REQUIRE_SMS_VERIFICATION']:
        return False

    user.phone_verification_code = '{:06d}'.format(
        random.randint(100000, 999999)
    )
    DB.session.commit()

    APP.sms_manager.send_template(
        user,
        'verification_code.sms',
        code=user.phone_verification_code
    )

    LOG.info('Sent phone verification code to %s', user.identifier)

    return True

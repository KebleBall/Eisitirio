# coding: utf-8
"""Script to prefill the database with colleges and affiliations."""

from __future__ import unicode_literals

import os
import uuid

from flask.ext import script

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.database import static
from eisitirio.helpers import photos

class PrefillCommand(script.Command):
    """Flask-Script command for prefilling the database."""

    help = 'Prefill database with colleges and affiliations'

    @staticmethod
    def run():
        """Prefill the database."""
        with app.APP.app_context():
            db.DB.session.add_all(static.COLLEGES)
            db.DB.session.add_all(static.AFFILIATIONS)

            if app.APP.config['REQUIRE_USER_PHOTO']:
                filename = str(uuid.uuid4()) + '.png'

                image_location = os.path.abspath(os.path.join(
                    os.path.dirname(__file__),
                    '..',
                    'static',
                    'images',
                    'eisitirio-logo.png'
                ))

                full_url, thumb_url = photos.upload_photo(filename,
                                                          image_location,
                                                          image_location)

                photo = models.Photo(filename, full_url, thumb_url)
            else:
                photo = None

            admin_user = models.User(
                'website@kebleball.com',
                'password',
                'Admin',
                'Anderson',
                '01234567890',
                static.COLLEGES[-1],
                static.AFFILIATIONS[-1],
                photo
            )

            admin_user.note = 'Automatically created admin user.\n'
            admin_user.role = 'Admin'
            admin_user.verified = True

            db.DB.session.add(admin_user)

            db.DB.session.commit()

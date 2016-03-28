# coding: utf-8
"""Views related to administrating photos."""

from __future__ import unicode_literals

from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import login_manager
from eisitirio.helpers import photos
from eisitirio.helpers import util

APP = app.APP
DB = db.DB

ADMIN_PHOTOS = flask.Blueprint('admin_photos', __name__)

@ADMIN_PHOTOS.route('/admin/photos/verify')
@login.login_required
@login_manager.admin_required
def verify_photos():
    """Allow an admin to verify photos."""
    photo = models.Photo.query.filter(
        models.Photo.verified == None # pylint: disable=singleton-comparison
    ).join(
        models.User.query.join(
            models.Ticket.query.filter(
                models.Ticket.cancelled == False # pylint: disable=singleton-comparison
            ).subquery(),
            models.User.tickets
        ).union(
            models.User.query.filter(
                models.User.held_ticket != None
            )
        ).subquery(),
        models.Photo.user
    ).first()

    if not photo:
        flask.flash('No photos to be verified!', 'success')

        return flask.redirect(flask.url_for('admin.admin_home'))

    return flask.render_template(
        'admin_photos/verify_photos.html',
        photo=photo,
        random=util.generate_key(5)
    )

@ADMIN_PHOTOS.route('/admin/photo/<int:photo_id>/reject')
@login.login_required
@login_manager.admin_required
def reject_photo(photo_id):
    """Reject a photo."""
    photo = models.Photo.get_by_id(photo_id)

    if not photo:
        flask.flash('No such photo', 'error')
    else:
        photo.verified = False

        APP.email_manager.send_template(
            photo.user.email,
            'Your photo has been rejected',
            'rejected_photo.email',
            name=photo.user.forenames,
            url=flask.url_for('dashboard.profile', _external=True)
        )

        DB.session.commit()

    return flask.redirect(flask.request.referrer or
                          flask.url_for('admin_photos.verify_photos'))

@ADMIN_PHOTOS.route('/admin/photo/<int:photo_id>/accept')
@login.login_required
@login_manager.admin_required
def accept_photo(photo_id):
    """Mark a photo as verified."""
    photo = models.Photo.get_by_id(photo_id)

    if not photo:
        flask.flash('No such photo', 'error')
    else:
        photo.verified = True

        DB.session.commit()

    return flask.redirect(flask.request.referrer or
                          flask.url_for('admin_photos.verify_photos'))

@ADMIN_PHOTOS.route('/admin/photo/<int:photo_id>/rotate/<int:degrees>')
@login.login_required
@login_manager.admin_required
def rotate_photo(photo_id, degrees):
    """Rotate a photo."""
    photo = models.Photo.get_by_id(photo_id)

    if not photo:
        flask.flash('No such photo', 'error')
    else:
        photos.rotate_photo(photo, degrees)

    return flask.redirect(flask.request.referrer or
                          flask.url_for('admin_photos.verify_photos'))

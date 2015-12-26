# coding: utf-8
"""Logic regarding verification of affiliations."""

import flask
import sqlalchemy

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

APP = app.APP
DB = db.DB

def verify_affiliation(user):
    """Mark the users affiliation as verified.

    For limited release, we require that the user's affiliation is verified.
    For current members with known battels accounts, this is done
    automatically, but for graduands, fellows, staff members etc an admin
    must manually check and approve them. This method is called when the
    affiliation is approved, and updates a flag before sending an email to
    the user reminding them to buy tickets.
    """
    user.affiliation_verified = True

    APP.email_manager.send_template(
        user.email,
        'Affiliation Verified - Buy Your Tickets Now!',
        'affiliation_verified.email',
        name=user.forenames,
        url=flask.url_for('purchase.purchase_home', _external=True)
    )

    DB.session.commit()

def deny_affiliation(user):
    """Mark the users affiliation as invalid.

    For limited release, we require that the user's affiliation is verified.
    For current members with known battels accounts, this is done
    automatically, but for graduands, fellows, staff members etc an admin
    must manually check and approve them. This method is called when the
    affiliation is rejected, and updates a flag accordingly.
    """
    user.affiliation_verified = False

    DB.session.commit()

def update_affiliation(user, new_college, new_affiliation):
    """Change the users affiliation.

    In order to maintain the verification of users' affiliations, when we
    update a college/affiliation we must re-submit it for verification as
    appropriate.
    """
    old_college = user.college
    old_affiliation = user.affiliation

    user.college = new_college
    user.affiliation = new_affiliation

    if (
            (
                old_affiliation != new_affiliation or
                old_college != new_college
            ) and
            new_college.name in APP.config['HOST_COLLEGES'] and
            new_affiliation.name not in [
                'Other',
                'None',
                'Graduate/Alumnus'
            ]
    ):
        user.affiliation_verified = None

def maybe_verify_affiliation(user):
    """Check if a user's affiliation can be verified

    Checks if a user's affiliation can be verified automatically, and
    otherwise sends an email to the ball ticketing officer to ask them to
    verify it manually
    """
    if (
            user.affiliation_verified is None and
            not APP.config['TICKETS_ON_SALE']
    ):
        if (
                user.college.name not in APP.config['HOST_COLLEGES'] or
                user.affiliation.name in [
                    'Other',
                    'None',
                    'Graduate/Alumnus'
                ] or
                (
                    user.affiliation.name == 'Student' and
                    user.battels_id is not None
                )
        ):
            user.affiliation_verified = True
            DB.session.commit()
            return

        APP.email_manager.send_template(
            APP.config['TICKETS_EMAIL'],
            'Verify Affiliation',
            'verify_affiliation.email',
            user=user,
            url=flask.url_for('admin_users.verify_affiliations',
                              _external=True)
        )
        flask.flash(
            (
                'Your affiliation must be verified before you will be '
                'able to purchase tickets. You will receive an email when '
                'your status has been verified.'
            ),
            'info'
        )

def get_unverified_users():
    """Get all the users who should be verified but aren't."""
    return models.User.query.filter(
        sqlalchemy.or_(
            models.User.college.has(name=college)
            for college in APP.config['HOST_COLLEGES']
        )
    ).filter(
        models.User.affiliation_verified == None
    ).all()

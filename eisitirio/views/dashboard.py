# coding: utf-8
"""Views for the users dashboard."""

from __future__ import unicode_literals

import datetime

import flask_login as login
# from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import photos
from eisitirio.helpers import util
from eisitirio.logic import affiliation_logic

APP = app.APP
DB = db.DB

DASHBOARD = flask.Blueprint('dashboard', __name__)

@DASHBOARD.route('/dashboard')
@login.login_required
def dashboard_home():
    """Display the users dashboard.

    Does nothing special.
    """
    return flask.render_template('dashboard/dashboard_home.html')

@DASHBOARD.route('/dashboard/profile', methods=['GET', 'POST'])
@login.login_required
def profile():
    """Show the user's personal details."""
    if not login.current_user.dietary_requirements:
        DB.session.add(models.DietaryRequirements(login.current_user))
        DB.session.commit()

    return flask.render_template(
        'dashboard/profile.html',
        colleges=models.College.query.all(),
        affiliations=models.Affiliation.query.all()
    )

@DASHBOARD.route('/dashboard/profile/update', methods=['GET', 'POST'])
@login.login_required
def update_profile():
    """Allow the user to update their personal details."""
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.profile'))

    if not login.current_user.can_update_details():
        flask.flash(
            flask.Markup(
                (
                    'You cannot currently change your details. Please contact '
                    '<a href="{0}">the ticketing officer</a> for assistance.'
                ).format(
                    APP.config['TICKETS_EMAIL_LINK']
                )
            ),
            'error'
        )

        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.profile'))

    flashes = []

    if (
            'forenames' not in flask.request.form or
            flask.request.form['forenames'] == ''
    ):
        flashes.append('Forename(s) cannot be blank')

    if (
            'surname' not in flask.request.form or
            flask.request.form['surname'] == ''
    ):
        flashes.append('Surname cannot be blank')

    if (
            'phone' not in flask.request.form or
            flask.request.form['phone'] == ''
    ):
        flashes.append('Phone cannot be blank')

    if (
            'college' not in flask.request.form or
            flask.request.form['college'] == '---'
    ):
        flashes.append('Please select a college')

    if (
            'affiliation' not in flask.request.form or
            flask.request.form['affiliation'] == '---'
    ):
        flashes.append('Please select an affiliation')

    if flashes:
        flask.flash(
            (
                'There were errors in your provided details. Please fix '
                'these and try again'
            ),
            'error'
        )

        for msg in flashes:
            flask.flash(msg, 'warning')

        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.profile'))

    login.current_user.forenames = flask.request.form['forenames']
    login.current_user.surname = flask.request.form['surname']

    if login.current_user.phone != flask.request.form['phone']:
        login.current_user.phone_verified = False
        login.current_user.phone = flask.request.form['phone']

    affiliation_logic.update_affiliation(
        login.current_user,
        models.College.get_by_id(flask.request.form['college']),
        models.Affiliation.get_by_id(flask.request.form['affiliation'])
    )

    DB.session.commit()

    APP.log_manager.log_event(
        'Updated Details',
        user=login.current_user
    )

    flask.flash(
        'Your details have been updated',
        'success'
    )

    affiliation_logic.maybe_verify_affiliation(login.current_user)

    return flask.redirect(flask.request.referrer or
                          flask.url_for('dashboard.profile'))

@DASHBOARD.route('/dashboard/dietary_requirements/update',
                 methods=['GET', 'POST'])
@login.login_required
def update_dietary_requirements():
    """Allow the user to update their dietary requirements."""
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.profile'))

    dietary_requirements = login.current_user.dietary_requirements

    for requirement in [
            'pescetarian',
            'vegetarian',
            'vegan',
            'gluten_free',
            'nut_free',
            'dairy_free',
            'egg_free',
            'seafood_free',
    ]:
        if (
                requirement in flask.request.form and
                flask.request.form[requirement] == 'Yes'
        ):
            setattr(dietary_requirements, requirement, True)
        else:
            setattr(dietary_requirements, requirement, False)

    if (
            'other' in flask.request.form and
            flask.request.form['other'] != ''
    ):
        dietary_requirements.other = flask.request.form['other']
    else:
        dietary_requirements.other = None

    DB.session.commit()

    APP.log_manager.log_event(
        'Updated dietary requirements',
        user=login.current_user
    )

    flask.flash(
        'Your dietary requirements have been updated',
        'success'
    )

    return flask.redirect(flask.request.referrer or
                          flask.url_for('dashboard.profile'))

@DASHBOARD.route('/dashboard/photo/update', methods=['GET', 'POST'])
@login.login_required
def update_photo():
    """Allow the user to update their photo."""
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.profile'))

    if not login.current_user.can_update_photo():
        flask.flash(
            flask.Markup(
                (
                    'You cannot currently change your photo. Please contact '
                    '<a href="{0}">the ticketing officer</a> for assistance.'
                ).format(
                    APP.config['TICKETS_EMAIL_LINK']
                )
            ),
            'error'
        )

        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.profile'))

    if (
            'photo' in flask.request.files and
            flask.request.files['photo'].filename != ''
    ):
        old_photo = login.current_user.photo

        new_photo = photos.save_photo(flask.request.files['photo'])

        login.current_user.photo = new_photo

        DB.session.delete(old_photo)
        DB.session.add(new_photo)

        DB.session.commit()

        # We don't want to delete the photo from S3 until after the DB has
        # been updated
        if old_photo is not None:
            photos.delete_photo(old_photo)

        APP.log_manager.log_event(
            'Updated photo',
            user=login.current_user
        )

        flask.flash(
            'Your photo has been updated',
            'success'
        )
    else:
        flask.flash('You must select a photo to upload.', 'warning')

    return flask.redirect(flask.request.referrer or
                          flask.url_for('dashboard.profile'))

@DASHBOARD.route('/dashboard/email/update', methods=['GET', 'POST'])
@login.login_required
def update_email():
    """Allow the user to update their email address."""
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.profile'))

    flashes = []

    if (
            flask.request.form['email'] != login.current_user.email and
            models.User.get_by_email(flask.request.form['email']) is not None
    ):
        flashes.append('That email address is already in use. ')

    if (
            'email' not in flask.request.form or
            flask.request.form['email'] == ''
    ):
        flashes.append('Email cannot be blank')

    if flashes:
        flask.flash(
            (
                'There were errors in your provided details. Please fix '
                'these and try again'
            ),
            'error'
        )

        for msg in flashes:
            flask.flash(msg, 'warning')

        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.profile'))

    if flask.request.form['email'] != login.current_user.email:
        login.current_user.new_email = flask.request.form['email']
        login.current_user.secret_key = util.generate_key(64)
        login.current_user.secret_key_expiry = (
            datetime.datetime.utcnow() + datetime.timedelta(days=7))

        APP.email_manager.send_template(
            flask.request.form['email'],
            'Confirm your Email Address',
            'email_change_confirm.email',
            name=login.current_user.forenames,
            confirmurl=flask.url_for(
                'front.confirm_email',
                user_id=login.current_user.object_id,
                secret_key=login.current_user.secret_key,
                _external=True
            )
        )

        flask.flash(
            (
                'You must confirm your new email address to make '
                'sure that we can contact you if necessary. Please '
                'check your email for further instructions.'
            ),
            'info'
        )

        DB.session.commit()

        APP.log_manager.log_event(
            'Updated email address',
            user=login.current_user
        )
    else:
        flask.flash('Your email has not been changed.', 'info')

    return flask.redirect(flask.request.referrer or
                          flask.url_for('dashboard.profile'))

@DASHBOARD.route('/dashboard/password/update', methods=['GET', 'POST'])
@login.login_required
def update_password():
    """Allow the user to update their password."""
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.profile'))

    flashes = []

    if (
            'oldpassword' not in flask.request.form or
            flask.request.form['oldpassword'] == ''
    ):
        flashes.append('Current password cannot be blank.')
    elif not login.current_user.check_password(
            flask.request.form['oldpassword']
    ):
        flashes.append('Current password is not correct.')

    if (
            'password' not in flask.request.form or
            'confirm' not in flask.request.form or
            flask.request.form['password'] == '' or
            flask.request.form['confirm'] == ''
    ):
        flashes.append('New passwords must not be blank.')
    else:
        if len(flask.request.form['password']) < 8:
            flashes.append('Password must be at least 8 characters long')

        if flask.request.form['password'] != flask.request.form['confirm']:
            flashes.append('New passwords do not match')

    if flashes:
        flask.flash(
            (
                'There were errors in your provided details. Please fix '
                'these and try again'
            ),
            'error'
        )

        for msg in flashes:
            flask.flash(msg, 'warning')

        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.profile'))

    login.current_user.set_password(flask.request.form['password'])

    DB.session.commit()

    APP.log_manager.log_event(
        'Updated password',
        user=login.current_user
    )

    flask.flash(
        'Your password has been updated',
        'success'
    )

    return flask.redirect(flask.request.referrer or
                          flask.url_for('dashboard.profile'))

@DASHBOARD.route('/dashboard/announcement/<int:announcement_id>')
@login.login_required
def display_announcement(announcement_id):
    """Display an announcement.

    The dashboard shows a condensed listing of announcements, this view allows
    the user to see an announcement in full.
    """
    announcement = models.Announcement.get_by_id(announcement_id)

    if not announcement:
        flask.flash(
            'Announcement {0} not found'.format(
                announcement_id
            ),
            'warning'
        )
        return flask.redirect(flask.url_for('dashboard.dashboard_home'))
    else:
        return flask.render_template(
            'dashboard/announcement.html',
            announcement=announcement
        )

@DASHBOARD.route('/dashboard/ticket/claim', methods=['GET', 'POST'])
@login.login_required
def claim_ticket():
    """Allow a user to claim a ticket for entry."""
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.dashboard_home'))

    if not login.current_user.can_claim_ticket():
        flask.flash('You are not eligible to claim a ticket.', 'error')
        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.dashboard_home'))

    if (
            'claim_code' not in flask.request.form or
            flask.request.form['claim_code'] == ''
    ):
        flask.flash('Invalid claim code.', 'error')
        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.dashboard_home'))

    ticket = models.Ticket.get_by_claim_code(flask.request.form['claim_code'])

    if not ticket:
        flask.flash('No ticket with given claim code.', 'error')
    elif not ticket.can_be_claimed():
        flask.flash(
            flask.Markup(
                (
                    'That ticket can not be claimed. Please contact '
                    '<a href="{0}">the ticketing officer</a> for assistance.'
                ).format(
                    APP.config['TICKETS_EMAIL_LINK']
                )
            ),
            'error'
        )
    else:
        ticket.holder = login.current_user
        ticket.claims_made += 1

        APP.log_manager.log_event(
            'Claimed ticket',
            user=login.current_user,
            tickets=[ticket]
        )

        DB.session.commit()

        flask.flash('Ticket claimed.', 'success')

    return flask.redirect(flask.request.referrer or
                          flask.url_for('dashboard.dashboard_home'))

@DASHBOARD.route('/dashboard/ticket/relinquish')
@login.login_required
def relinquish_ticket():
    """Allow a ticket holder to relinquish their ticket."""
    if not login.current_user.has_held_ticket():
        flask.flash('You do not hold a ticket to relinquish.', 'error')
    else:
        login.current_user.held_ticket.holder = None
        DB.session.commit()

        flask.flash('Ticket relinquished.', 'success')

    return flask.redirect(flask.request.referrer or
                          flask.url_for('dashboard.dashboard_home'))

@DASHBOARD.route('/dashboard/ticket/<int:ticket_id>/reclaim')
@login.login_required
def reclaim_ticket(ticket_id):
    """Allow a ticket owner to reclaim a claimed ticket."""
    ticket = models.Ticket.get_by_id(ticket_id)

    if not ticket:
        flask.flash('No such ticket.', 'error')
    elif ticket.holder is None:
        flask.flash('That ticket has not been claimed.', 'error')
    else:
        ticket.holder = None
        DB.session.commit()

        flask.flash('Ticket reclaimed.', 'success')

    return flask.redirect(flask.request.referrer or
                          flask.url_for('dashboard.dashboard_home'))

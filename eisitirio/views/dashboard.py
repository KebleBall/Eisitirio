# coding: utf-8
"""Views for the users dashboard."""

from __future__ import unicode_literals

import datetime

from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
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
    """Allow the user to edit their personal details.

    Displays a form and processes it to update the users details.
    """
    if flask.request.method == 'POST':
        valid = True
        flashes = []

        if (
                flask.request.form['email'] != login.current_user.email and
                models.User.get_by_email(
                    flask.request.form['email']
                ) is not None
        ):
            flashes.append('That email address is already in use. ')
            valid = False

        if (
                'oldpassword' in flask.request.form and
                flask.request.form['oldpassword'] != ''
        ):
            if not login.current_user.check_password(
                    flask.request.form['oldpassword']
            ):
                flashes.append('Current password is not correct')
                valid = False

            if (
                    'password' not in flask.request.form or
                    'confirm' not in flask.request.form or
                    flask.request.form['password'] == '' or
                    (
                        flask.request.form['password'] !=
                        flask.request.form['confirm']
                    )
            ):
                flashes.append('New passwords do not match')
                valid = False

            if len(flask.request.form['password']) < 8:
                flashes.append('Password must be at least 8 characters long')
                valid = False

        if (
                'forenames' not in flask.request.form or
                flask.request.form['forenames'] == ''
        ):
            flashes.append('First Name cannot be blank')
            valid = False

        if (
                'surname' not in flask.request.form or
                flask.request.form['surname'] == ''
        ):
            flashes.append('Surname cannot be blank')
            valid = False

        if (
                'email' not in flask.request.form or
                flask.request.form['email'] == ''
        ):
            flashes.append('Email cannot be blank')
            valid = False

        if (
                'phone' not in flask.request.form or
                flask.request.form['phone'] == ''
        ):
            flashes.append('Phone cannot be blank')
            valid = False

        if (
                'college' not in flask.request.form or
                flask.request.form['college'] == '---'
        ):
            flashes.append('Please select a college')
            valid = False

        if (
                'affiliation' not in flask.request.form or
                flask.request.form['affiliation'] == '---'
        ):
            flashes.append('Please select an affiliation')
            valid = False

        if not valid:
            flask.flash(
                (
                    'There were errors in your provided details. Please fix '
                    'these and try again'
                ),
                'error'
            )
            for msg in flashes:
                flask.flash(msg, 'warning')
        else:
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

            if (
                    'oldpassword' in flask.request.form and
                    flask.request.form['oldpassword'] != ''
            ):
                login.current_user.set_password(flask.request.form['password'])

            login.current_user.forenames = flask.request.form['forenames']
            login.current_user.surname = flask.request.form['surname']
            login.current_user.phone = flask.request.form['phone']

            affiliation_logic.update_affiliation(
                login.current_user,
                models.College.get_by_id(flask.request.form['college']),
                models.Affiliation.get_by_id(flask.request.form['affiliation'])
            )

            DB.session.commit()

            APP.log_manager.log_event(
                'Updated Details',
                [],
                login.current_user
            )

            flask.flash(
                'Your details have been updated',
                'success'
            )

            affiliation_logic.maybe_verify_affiliation(login.current_user)

    return flask.render_template(
        'dashboard/profile.html',
        colleges=models.College.query.all(),
        affiliations=models.Affiliation.query.all()
    )

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

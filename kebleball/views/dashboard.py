# coding: utf-8
"""Views for the users dashboard."""

from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask.ext import login

from kebleball import app
from kebleball.database import db
from kebleball.database import models
from kebleball.helpers import generate_key

APP = app.APP
DB = db.DB

DASHBOARD = Blueprint('dashboard', __name__)

@DASHBOARD.route('/dashboard')
@login.login_required
def dashboard_home():
    """Display the users dashboard.

    Does nothing special.
    """
    return render_template('dashboard/dashboard_home.html')

@DASHBOARD.route('/dashboard/profile', methods=['GET', 'POST'])
@login.login_required
def profile():
    """Allow the user to edit their personal details.

    Displays a form and processes it to update the users details.
    """
    if request.method == 'POST':
        valid = True
        flashes = []

        if (
                request.form['email'] != login.current_user.email and
                models.User.get_by_email(request.form['email']) is not None
        ):
            flashes.append(u'That email address is already in use. ')
            valid = False

        if (
                'oldpassword' in request.form and
                request.form['oldpassword'] != ''
        ):
            if not login.current_user.check_password(
                    request.form['oldpassword']):
                flashes.append(u'Current password is not correct')
                valid = False

            if (
                    'password' not in request.form or
                    'confirm' not in request.form or
                    request.form['password'] == '' or
                    request.form['password'] != request.form['confirm']
            ):
                flashes.append(u'New passwords do not match')
                valid = False

            if len(request.form['password']) < 8:
                flashes.append(u'Password must be at least 8 characters long')
                valid = False

        if (
                'forenames' not in request.form or
                request.form['forenames'] == ''
        ):
            flashes.append(u'First Name cannot be blank')
            valid = False

        if (
                'surname' not in request.form or
                request.form['surname'] == ''
        ):
            flashes.append(u'Surname cannot be blank')
            valid = False

        if (
                'email' not in request.form or
                request.form['email'] == ''
        ):
            flashes.append(u'Email cannot be blank')
            valid = False

        if (
                'phone' not in request.form or
                request.form['phone'] == ''
        ):
            flashes.append(u'Phone cannot be blank')
            valid = False

        if (
                'college' not in request.form or
                request.form['college'] == '---'
        ):
            flashes.append(u'Please select a college')
            valid = False

        if (
                'affiliation' not in request.form or
                request.form['affiliation'] == '---'
        ):
            flashes.append(u'Please select an affiliation')
            valid = False

        if not valid:
            flash(
                (
                    u'There were errors in your provided details. Please fix '
                    u'these and try again'
                ),
                'error'
            )
            for msg in flashes:
                flash(msg, 'warning')
        else:
            if request.form['email'] != login.current_user.email:
                login.current_user.new_email = request.form['email']
                login.current_user.secret_key = generate_key(64)
                login.current_user.secret_key_expiry = (
                    datetime.utcnow() + timedelta(days=7))

                APP.email_manager.send_template(
                    request.form['email'],
                    'Confirm your Email Address',
                    'emailChangeConfirm.email',
                    confirmurl=url_for(
                        'front.confirm_email',
                        user_id=login.current_user.object_id,
                        secret_key=login.current_user.secret_key,
                        _external=True
                    )
                )

                flash(
                    (
                        u'You must confirm your new email address to make '
                        u'sure that we can contact you if necessary. Please '
                        u'check your email for further instructions.'
                    ),
                    'info'
                )

            if (
                    'oldpassword' in request.form and
                    request.form['oldpassword'] != ''
            ):
                login.current_user.set_password(request.form['password'])

            login.current_user.forenames = request.form['forenames']
            login.current_user.surname = request.form['surname']
            login.current_user.phone = request.form['phone']
            login.current_user.college_id = request.form['college']
            login.current_user.update_affiliation(request.form['affiliation'])

            db.session.commit()

            APP.log_manager.log_event(
                'Updated Details',
                [],
                login.current_user
            )

            flash(
                u'Your details have been updated',
                'success'
            )

            login.current_user.maybe_verify_affiliation()

    return render_template(
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
        flash(
            u'Announcement {0} not found'.format(
                announcement_id
            ),
            'warning'
        )
        return redirect(url_for('dashboard.dashboard_home'))
    else:
        return render_template(
            'dashboard/announcement.html',
            announcement=announcement
        )

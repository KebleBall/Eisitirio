# coding: utf-8
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask.ext.login import login_required, current_user

from kebleball.app import app
from kebleball.database import db
from kebleball.database.college import College
from kebleball.database.affiliation import Affiliation
from kebleball.database.announcement import Announcement
from kebleball.database.user import User
from kebleball.helpers import generate_key
from datetime import datetime, timedelta

log = app.log_manager.log_dashboard
log_event = app.log_manager.log_event

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard')
@login_required
def dashboardHome():
    return render_template('dashboard/dashboardHome.html')

@dashboard.route('/dashboard/profile', methods=['GET','POST'])
@login_required
def profile():
    if request.method == 'POST':
        valid = True
        flashes = []

        if (
            request.form['email'] != current_user.email and
            User.get_by_email(request.form['email']) is not None
        ):
            flashes.append(u'That email address is already in use. ')
            valid = False

        if (
            'oldpassword' in request.form and
            request.form['oldpassword'] != ''
        ):
            if not current_user.checkPassword(request.form['oldpassword']):
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
            'firstname' not in request.form or
            request.form['firstname'] == ''
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
            if request.form['email'] != current_user.email:
                current_user.newemail = request.form['email']
                current_user.secretkey = generate_key(64)
                current_user.secretkeyexpiry = datetime.utcnow() + timedelta(days=7)

                app.email_manager.sendTemplate(
                    request.form['email'],
                    "Confirm your Email Address",
                    "emailChangeConfirm.email",
                    confirmurl=url_for(
                        'front.confirmEmail',
                        userID=current_user.id,
                        secretkey=current_user.secretkey,
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
                request.form['oldpassword'] != ""
            ):
                current_user.setPassword(request.form['password'])

            current_user.firstname = request.form['firstname']
            current_user.surname = request.form['surname']
            current_user.affiliation_id = request.form['phone']
            current_user.college_id = request.form['college']
            current_user.affiliation_id = request.form['affiliation']

            db.session.commit()

            log_event(
                'Updated Details',
                [],
                current_user
            )

            flash(
                u'Your details have been updated',
                'success'
            )

    return render_template(
        'dashboard/profile.html',
        colleges = College.query.all(),
        affiliations = Affiliation.query.all()
    )

@dashboard.route('/dashboard/announcement/<int:announcementID>')
@login_required
def announcement(announcementID):
    announcement = Announcement.get_by_id(announcementID)

    if not announcement:
        flash(
            u'Announcement {0} not found'.format(
                announcementID
            ),
            'warning'
        )
        return redirect(url_for('dashboard.dashboardHome'))
    else:
        return render_template(
            'dashboard/announcement.html',
            announcement=announcement
        )
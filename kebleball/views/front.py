# coding: utf-8
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from flask.ext.login import login_user, logout_user, login_required, current_user

from kebleball.app import app
from kebleball.helpers import generate_key
from kebleball.database import db
from kebleball.database.user import User
from kebleball.database.college import College
from kebleball.database.affiliation import Affiliation

from datetime import datetime, timedelta

log = app.log_manager.log_front
log_event = app.log_manager.log_event

front = Blueprint('front', __name__)

@front.route('/home')
def home():
    return render_template(
        'front/home.html',
        colleges = College.query.all(),
        affiliations = Affiliation.query.all(),
        form={}
    )

@front.route('/login', methods=['POST'])
def login():
    user = User.get_by_email(request.form['email'])

    if not user or not user.checkPassword(request.form['password']):
        if user:
            log_event(
                'Failed login attempt - invalid password',
                None,
                user
            )

        flash(u'Could not complete log in. Invalid email or password.', 'error')
        return redirect(url_for('front.home'))

    if not user.verified:
        log_event(
            'Failed login attempt - not verified',
            None,
            user
        )
        flash(
            u'Could not complete log in. Email address is not confirmed.',
            'warning'
        )
        return redirect(url_for('front.home'))

    login_user(
        user,
        remember=(
            'remember-me' in request.form and
            request.form['remember-me'] == 'yes'
        )
    )

    log_event(
        'Logged in',
        None,
        user
    )

    flash(u'Logged in successfully.', 'success')
    return redirect(request.form.get('next', False) or url_for("dashboard.dashboardHome"))

@front.route('/register', methods=['POST'])
def register():
    valid = True
    flashes = []

    if User.get_by_email(request.form['email']) is not None:
        flash(
            (
                u'That email address already has an associated account. '
                u'Use the links below to verify your email or reset your '
                u'password.'
            ),
            'error'
        )
        return render_template(
            'front/home.html',
            colleges = College.query.all(),
            affiliations = Affiliation.query.all(),
            form={}
        )

    if (
        'password' not in request.form or
        'confirm' not in request.form or
        request.form['password'] != request.form['confirm']
    ):
        flashes.append(u'Passwords do not match')
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
        'password' not in request.form or
        request.form['password'] == ''
    ):
        flashes.append(u'Password cannot be blank')
        valid = False
    elif len(request.form['password']) < 8:
        flashes.append(u'Password must be at least 8 characters long')
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

        return render_template(
            'front/home.html',
            form=request.form,
            colleges = College.query.all(),
            affiliations = Affiliation.query.all()
        )

    user = User(
        request.form['email'],
        request.form['password'],
        request.form['firstname'],
        request.form['surname'],
        request.form['phone'],
        request.form['college'],
        request.form['affiliation']
    )

    db.session.add(user)
    db.session.commit()

    log_event(
        'Registered',
        None,
        user
    )

    app.email_manager.sendTemplate(
        request.form['email'],
        "Confirm your Email Address",
        "emailConfirm.email",
        confirmurl=url_for(
            'front.confirmEmail',
            userID=user.id,
            secretkey=user.secretkey,
            _external=True
        ),
        destroyurl=url_for(
            'front.destroyAccount',
            userID=user.id,
            secretkey=user.secretkey,
            _external=True
        )
    )

    flash(u'Your user account has been registered', 'success')
    flash(
        (
            u'Before you can log in, you must confirm your email address. '
            u'Please check your email for further instructions.'
        ),
        'info'
    )
    return redirect(url_for('front.home'))

@front.route('/terms')
def terms():
    return render_template('front/terms.html')

@front.route('/passwordreset', methods=['GET','POST'])
def passwordReset():
    if request.method == 'POST':
        user = User.get_by_email(request.form['email'])

        if not user:
            log_event(
                'Attempted password reset for {0}'.format(
                    request.form['email']
                )
            )

            app.email_manager.sendTemplate(
                request.form['email'],
                "Attempted Account Access",
                "passwordResetFail.email"
            )
        else:
            log_event(
                'Started password reset',
                None,
                user
            )

            user.secretkey = generate_key(64)
            user.secretkeyexpiry = (
                datetime.utcnow() +
                timedelta(minutes=30)
            )

            db.session.commit()

            app.email_manager.sendTemplate(
                request.form['email'],
                "Confirm Password Reset",
                "passwordResetConfirm.email",
                confirmurl=url_for(
                    'front.resetPassword',
                    userID=user.id,
                    secretkey=user.secretkey,
                    _external=True
                )
            )

        flash(
            (
                u'An email has been sent to {0} with detailing what to do '
                u'next. Please check your email (including your spam folder) '
                u'and follow the instructions given'
            ).format(
                request.form['email']
            ),
            'info'
        )

        return redirect(url_for('front.home'))
    else:
        return render_template('front/passwordReset.html')

@front.route('/emailconfirm', methods=['GET','POST'])
def emailConfirm():
    if request.method == 'POST':
        user = User.get_by_email(request.form['email'])

        if not user:
            log_event(
                'Attempted email confirm for {0}'.format(
                    request.form['email']
                )
            )

            app.email_manager.sendTemplate(
                request.form['email'],
                "Attempted Account Access",
                "emailConfirmFail.email"
            )
        else:
            log_event(
                'Requested email confirm',
                None,
                user
            )

            user.secretkey = generate_key(64)
            user.secretkeyexpiry = None

            db.session.commit()

            app.email_manager.sendTemplate(
                request.form['email'],
                "Confirm your Email Address",
                "emailConfirm.email",
                confirmurl=url_for(
                    'front.confirmEmail',
                    userID=user.id,
                    secretkey=user.secretkey,
                    _external=True
                ),
                destroyurl=url_for(
                    'front.destroyAccount',
                    userID=user.id,
                    secretkey=user.secretkey,
                    _external=True
                )
            )

        flash(
            (
                u'An email has been sent to {0} with detailing what to do '
                u'next. Please check your email (including your spam folder) '
                u'and follow the instructions given'
            ).format(
                request.form['email']
            ),
            'info'
        )

        return redirect(url_for('front.home'))
    else:
        return render_template('front/emailConfirm.html')

@front.route('/resetpassword/<int:userID>/<secretkey>', methods=['GET', 'POST'])
def resetPassword(userID, secretkey):
    user = User.get_by_id(userID)

    if user is None or user.secretkey != secretkey:
        user.secretkey = None
        user.secretkeyexpiry = None
        db.session.commit()
        flash(u'Could not complete password reset. Please try again','error')
        return redirect(url_for('front.home'))

    if request.method == 'POST':
        if request.form['password'] != request.form['confirm']:
            user.secretkey = generate_key(64)
            user.secretkeyexpiry = datetime.utcnow() + timedelta(minutes=5)
            db.session.commit()
            flash(u'Passwords do not match, please try again', 'warning')
            return redirect(
                url_for(
                    'front.resetPassword',
                    userID=user.id,
                    secretkey=user.secretkey
                )
            )
        else:
            log_event(
                'Completed password reset',
                None,
                user
            )

            user.setPassword(request.form['password'])
            user.secretkey = None
            user.secretkeyexpiry = None
            db.session.commit()
            flash(u'Your password has been reset, please log in.','success')
            return redirect(url_for('front.home'))
    else:
        return render_template('front/resetPassword.html')

@front.route('/confirmemail/<int:userID>/<secretkey>')
def confirmEmail(userID, secretkey):
    user = User.get_by_id(userID)

    if user is not None and user.secretkey == secretkey:
        log_event(
            'Confirmed email',
            None,
            user
        )

        user.secretkey = None
        user.verified = True

        if user.newemail is not None:
            user.email = user.newemail
            user.newemail = None

        db.session.commit()
        flash(u'Your email address has been verified. You can now log in','info')
    else:
        flash(u'Could not confirm email address. Check that you have used the correct link','warning')

    return redirect(url_for('front.home'))

@front.route('/destroyaccount/<int:userID>/<secretkey>')
def destroyAccount(userID, secretkey):
    user = User.get_by_id(userID)

    if user is not None and user.secretkey == secretkey:
        if not user.is_verified():
            log_event(
                'Deleted account with email address {0}'.format(
                    user.email
                )
            )

            for entry in user.events:
                entry.message = (
                    entry.message +
                    " (destroyed user with email address {0})".format(
                        self.email
                    )
                )
                entry.user = None

            db.session.delete(user)
            db.session.commit()

            flash(u'The account has been deleted.','info')
        else:
            log_event(
                'Attempted deletion of verified account',
                None,
                user
            )

            flash(u'Could not delete user account.','warning')
    else:
        flash(u'Could not delete user account. Check that you have used the correct link','warning')

    return redirect(url_for('front.home'))

@front.route('/logout')
@login_required
def logout():
    log_event(
        'Logged Out',
        None,
        current_user
    )

    logout_user()
    return redirect(url_for('front.home'))
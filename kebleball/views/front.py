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

#Not constants but functions
log = app.log_manager.log_front
log_event = app.log_manager.log_event

FRONT = Blueprint('front', __name__)

@FRONT.route('/home')
def home():
    return render_template(
        'front/home.html',
        colleges=College.query.all(),
        affiliations=Affiliation.query.all(),
        form={}
    )

@FRONT.route('/login', methods=['POST'])
def login():
    user = User.get_by_email(request.form['email'])

    if not user or not user.check_password(request.form['password']):
        if user:
            log_event(
                'Failed login attempt - invalid password',
                [],
                user
            )
        else:
            log_event(
                'Failed login attempt - invalid email {0}'.format(
                    request.form['email']
                ),
                [],
                None
            )

        flash(u'Could not complete log in. Invalid email or password.', 'error')
        return redirect(url_for('front.home'))

    if not user.verified:
        log_event(
            'Failed login attempt - not verified',
            [],
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
        [],
        user
    )

    flash(u'Logged in successfully.', 'success')
    return redirect(request.form.get('next', False)
                    or url_for("dashboard.dashboard_home"))

@FRONT.route('/register', methods=['POST'])
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
        return redirect(url_for('front.home'))

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
            colleges=College.query.all(),
            affiliations=Affiliation.query.all()
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
        [],
        user
    )

    app.email_manager.sendTemplate(
        request.form['email'],
        "Confirm your Email Address",
        "emailConfirm.email",
        confirmurl=url_for(
            'front.confirm_email',
            user_id=user.id,
            secretkey=user.secretkey,
            _external=True
        ),
        destroyurl=url_for(
            'front.destroy_account',
            user_id=user.id,
            secretkey=user.secretkey,
            _external=True
        )
    )

    flash(u'Your user account has been registered', 'success')
    flash(
        (
            u'Before you can log in, you must confirm your email address. '
            u'Please check your email for further instructions. If the message '
            u'does not arrive, please check your spam/junk mail folder.'
        ),
        'info'
    )

    user.maybe_verify_affiliation()

    return redirect(url_for('front.home'))

@FRONT.route('/terms')
def terms():
    return render_template('front/terms.html')

@FRONT.route('/passwordreset', methods=['GET', 'POST'])
def password_reset():
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
            user.secretkey = generate_key(64)
            user.secretkeyexpiry = (
                datetime.utcnow() +
                timedelta(minutes=30)
            )

            db.session.commit()

            log_event(
                'Started password reset',
                [],
                user
            )

            app.email_manager.sendTemplate(
                request.form['email'],
                "Confirm Password Reset",
                "passwordResetConfirm.email",
                confirmurl=url_for(
                    'front.reset_password',
                    user_id=user.id,
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
        return render_template('front/password_reset.html')

@FRONT.route('/emailconfirm', methods=['GET', 'POST'])
def email_confirm():
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
            user.secretkey = generate_key(64)
            user.secretkeyexpiry = None

            db.session.commit()

            log_event(
                'Requested email confirm',
                [],
                user
            )

            app.email_manager.sendTemplate(
                request.form['email'],
                "Confirm your Email Address",
                "emailConfirm.email",
                confirmurl=url_for(
                    'front.confirm_email',
                    user_id=user.id,
                    secretkey=user.secretkey,
                    _external=True
                ),
                destroyurl=url_for(
                    'front.destroy_account',
                    user_id=user.id,
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
        return render_template('front/email_confirm.html')

@FRONT.route('/resetpassword/<int:user_id>/<secretkey>', methods=['GET', 'POST'])
def reset_password(user_id, secretkey):
    user = User.get_by_id(user_id)

    if user is None or user.secretkey != secretkey:
        user.secretkey = None
        user.secretkeyexpiry = None
        db.session.commit()
        flash(u'Could not complete password reset. Please try again', 'error')
        return redirect(url_for('front.home'))

    if request.method == 'POST':
        if request.form['password'] != request.form['confirm']:
            user.secretkey = generate_key(64)
            user.secretkeyexpiry = datetime.utcnow() + timedelta(minutes=5)
            db.session.commit()
            flash(u'Passwords do not match, please try again', 'warning')
            return redirect(
                url_for(
                    'front.reset_password',
                    user_id=user.id,
                    secretkey=user.secretkey
                )
            )
        else:
            user.set_password(request.form['password'])
            user.secretkey = None
            user.secretkeyexpiry = None
            db.session.commit()

            log_event(
                'Completed password reset',
                [],
                user
            )

            flash(u'Your password has been reset, please log in.', 'success')
            return redirect(url_for('front.home'))
    else:
        return render_template(
            'front/reset_password.html',
            user_id=user_id,
            secretkey=secretkey
        )

@FRONT.route('/confirmemail/<int:user_id>/<secretkey>')
def confirm_email(user_id, secretkey):
    user = User.get_by_id(user_id)

    if user is not None and user.secretkey == secretkey:
        user.secretkey = None
        user.verified = True

        if user.newemail is not None:
            user.email = user.newemail
            user.newemail = None

        db.session.commit()

        log_event(
            'Confirmed email',
            [],
            user
        )

        flash(u'Your email address has been verified. You can now log in',
              'info')
    else:
        flash(u'Could not confirm email address. Check that you have used the correct link', 'warning')

    return redirect(url_for('front.home'))

@FRONT.route('/destroyaccount/<int:user_id>/<secretkey>')
def destroy_account(user_id, secretkey):
    user = User.get_by_id(user_id)

    if user is not None and user.secretkey == secretkey:
        if not user.is_verified():
            for entry in user.events:
                entry.action = (
                    entry.action +
                    " (destroyed user with email address {0})".format(
                        self.email
                    )
                )
                entry.user = None

            db.session.delete(user)
            db.session.commit()

            log_event(
                'Deleted account with email address {0}'.format(
                    user.email
                )
            )

            flash(u'The account has been deleted.', 'info')
        else:
            log_event(
                'Attempted deletion of verified account',
                [],
                user
            )

            flash(u'Could not delete user account.', 'warning')
    else:
        flash(u'Could not delete user account. Check that you have used the correct link', 'warning')

    return redirect(url_for('front.home'))

@FRONT.route('/logout')
@login_required
def logout():
    if 'actor_id' in session:
        log_event(
            'Finished impersonating user',
            [],
            current_user
        )

        actor = User.get_by_id(session['actor_id'])

        if actor:
            login_user(
                actor
            )

            return redirect(url_for('admin.admin_home'))

    log_event(
        'Logged Out',
        [],
        current_user
    )

    logout_user()
    return redirect(url_for('front.home'))

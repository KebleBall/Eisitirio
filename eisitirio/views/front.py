# coding: utf-8
"""Views related to users who aren't logged in."""

from __future__ import unicode_literals

import datetime

from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import photos
from eisitirio.helpers import util
from eisitirio.logic import affiliation_logic

APP = app.APP
DB = db.DB

FRONT = flask.Blueprint('front', __name__)

@FRONT.route('/home')
def home():
    """Display the homepage.

    Contains forms for registering and logging in.
    """
    return flask.render_template(
        'front/home.html',
        colleges=models.College.query.all(),
        affiliations=models.Affiliation.query.all(),
        form={}
    )

@FRONT.route('/login', methods=['GET', 'POST'])
def do_login():
    """Process a login."""
    if flask.request.method != 'POST':
        return flask.redirect(flask.url_for('router'))

    user = models.User.get_by_email(flask.request.form['email'])

    if not user or not user.check_password(flask.request.form['password']):
        if user:
            APP.log_manager.log_event(
                'Failed login attempt - invalid password',
                [],
                user
            )
        else:
            APP.log_manager.log_event(
                'Failed login attempt - invalid email {0}'.format(
                    flask.request.form['email']
                ),
                [],
                None
            )

        flask.flash(
            'Could not complete log in. Invalid email or password.',
            'error'
        )
        return flask.redirect(flask.url_for('front.home'))

    if not user.verified:
        APP.log_manager.log_event(
            'Failed login attempt - not verified',
            [],
            user
        )
        flask.flash(
            'Could not complete log in. Email address is not confirmed.',
            'warning'
        )
        return flask.redirect(flask.url_for('front.home'))

    login.login_user(
        user,
        remember=(
            'remember-me' in flask.request.form and
            flask.request.form['remember-me'] == 'yes'
        )
    )

    APP.log_manager.log_event(
        'Logged in',
        [],
        user
    )

    flask.flash('Logged in successfully.', 'success')
    return flask.redirect(flask.request.form.get('next', False) or
                          flask.url_for('dashboard.dashboard_home'))

@FRONT.route('/register', methods=['GET', 'POST'])
def register():
    """Process a registration.

    After registration, the user must click a link in an email sent to the
    address they registered with to confirm that it is valid.
    """
    if flask.request.method != 'POST':
        return flask.redirect(flask.url_for('router'))

    flashes = []

    if models.User.get_by_email(flask.request.form['email']) is not None:
        flask.flash(
            (
                'That email address already has an associated account. '
                'Use the links below to verify your email or reset your '
                'password.'
            ),
            'error'
        )
        return flask.redirect(flask.url_for('front.home'))

    if (
            'password' not in flask.request.form or
            'confirm' not in flask.request.form or
            flask.request.form['password'] != flask.request.form['confirm']
    ):
        flashes.append('Passwords do not match')

    if (
            'forenames' not in flask.request.form or
            flask.request.form['forenames'] == ''
    ):
        flashes.append('Forenames cannot be blank')

    if (
            'surname' not in flask.request.form or
            flask.request.form['surname'] == ''
    ):
        flashes.append('Surname cannot be blank')

    if (
            'email' not in flask.request.form or
            flask.request.form['email'] == ''
    ):
        flashes.append('Email cannot be blank')

    if (
            'password' not in flask.request.form or
            flask.request.form['password'] == ''
    ):
        flashes.append('Password cannot be blank')
    elif len(flask.request.form['password']) < 8:
        flashes.append('Password must be at least 8 characters long')

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

    if APP.config['REQUIRE_USER_PHOTO'] and (
            'photo' not in flask.request.files or
            flask.request.files['photo'].filename == ''
    ):
        flashes.append('Please upload a photo')

    if 'accept_terms' not in flask.request.form:
        flashes.append('You must accept the Terms and Conditions')

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

        return flask.render_template(
            'front/home.html',
            form=flask.request.form,
            colleges=models.College.query.all(),
            affiliations=models.Affiliation.query.all()
        )

    if APP.config['REQUIRE_USER_PHOTO']:
        photo = photos.save_photo(flask.request.files['photo'])

        DB.session.add(photo)
        DB.session.commit()
    else:
        photo = None

    user = models.User(
        flask.request.form['email'],
        flask.request.form['password'],
        flask.request.form['forenames'],
        flask.request.form['surname'],
        flask.request.form['phone'],
        models.College.get_by_id(flask.request.form['college']),
        models.Affiliation.get_by_id(flask.request.form['affiliation']),
        photo
    )

    DB.session.add(user)
    DB.session.commit()

    APP.log_manager.log_event(
        'Registered',
        [],
        user
    )

    APP.email_manager.send_template(
        flask.request.form['email'],
        'Confirm your Email Address',
        'email_confirm.email',
        name=user.forenames,
        confirmurl=flask.url_for(
            'front.confirm_email',
            user_id=user.object_id,
            secret_key=user.secret_key,
            _external=True
        ),
        destroyurl=flask.url_for(
            'front.destroy_account',
            user_id=user.object_id,
            secret_key=user.secret_key,
            _external=True
        )
    )

    flask.flash('Your user account has been registered', 'success')
    flask.flash(
        (
            'Before you can log in, you must confirm your email address. '
            'Please check your email for further instructions. If the message '
            'does not arrive, please check your spam/junk mail folder.'
        ),
        'info'
    )

    affiliation_logic.maybe_verify_affiliation(user)

    return flask.redirect(flask.url_for('front.home'))

@FRONT.route('/confirmemail/<int:user_id>/<secret_key>')
def confirm_email(user_id, secret_key):
    """Confirm the user's email address.

    The user is sent a link to this view in an email. Visiting this view
    confirms the validity of their email address.
    """
    user = models.User.get_by_id(user_id)

    if user is not None and user.secret_key == secret_key:
        user.secret_key = None
        user.verified = True

        # This view is used to verify the email address if an already registered
        # user decides to change their registered email.
        if user.new_email is not None:
            user.email = user.new_email
            user.new_email = None

        DB.session.commit()

        APP.log_manager.log_event(
            'Confirmed email',
            [],
            user
        )

        if login.current_user.is_anonymous:
            flask.flash(
                'Your email address has been verified. You can now log in',
                'info'
            )
        else:
            flask.flash('Your email address has been verified.', 'info')
    else:
        flask.flash(
            (
                'Could not confirm email address. Check that you have used '
                'the correct link'
            ),
            'warning'
        )

    return flask.redirect(flask.url_for('router'))

@FRONT.route('/emailconfirm', methods=['GET', 'POST'])
def email_confirm():
    """Retry email confirmation.

    If the user somehow manages to lose the email confirmation message, they can
    use this view to have it resent.
    """
    if flask.request.method == 'POST':
        user = models.User.get_by_email(flask.request.form['email'])

        if not user:
            APP.log_manager.log_event(
                'Attempted email confirm for {0}'.format(
                    flask.request.form['email']
                )
            )

            APP.email_manager.send_template(
                flask.request.form['email'],
                'Attempted Account Access',
                'email_confirm_fail.email'
            )
        else:
            user.secret_key = util.generate_key(64)
            user.secret_key_expiry = None

            DB.session.commit()

            APP.log_manager.log_event(
                'Requested email confirm',
                [],
                user
            )

            APP.email_manager.send_template(
                flask.request.form['email'],
                'Confirm your Email Address',
                'email_confirm.email',
                name=user.forenames,
                confirmurl=flask.url_for(
                    'front.confirm_email',
                    user_id=user.object_id,
                    secret_key=user.secret_key,
                    _external=True
                ),
                destroyurl=flask.url_for(
                    'front.destroy_account',
                    user_id=user.object_id,
                    secret_key=user.secret_key,
                    _external=True
                )
            )

        flask.flash(
            (
                'An email has been sent to {0} with detailing what to do '
                'next. Please check your email (including your spam folder) '
                'and follow the instructions given'
            ).format(
                flask.request.form['email']
            ),
            'info'
        )

        return flask.redirect(flask.url_for('front.home'))
    else:
        return flask.render_template('front/email_confirm.html')

@FRONT.route('/terms')
def terms():
    """Display the terms and conditions."""
    return flask.render_template('front/terms.html')

@FRONT.route('/passwordreset', methods=['GET', 'POST'])
def password_reset():
    """Display a form to start the password reset process.

    User enters their email, and is sent an email containing a link with a
    random key to validate their identity.
    """
    if flask.request.method == 'POST':
        user = models.User.get_by_email(flask.request.form['email'])

        if not user:
            APP.log_manager.log_event(
                'Attempted password reset for {0}'.format(
                    flask.request.form['email']
                )
            )

            APP.email_manager.send_template(
                flask.request.form['email'],
                'Attempted Account Access',
                'password_reset_fail.email'
            )
        else:
            user.secret_key = util.generate_key(64)
            user.secret_key_expiry = (
                datetime.datetime.utcnow() +
                datetime.timedelta(minutes=30)
            )

            DB.session.commit()

            APP.log_manager.log_event(
                'Started password reset',
                [],
                user
            )

            APP.email_manager.send_template(
                flask.request.form['email'],
                'Confirm Password Reset',
                'password_reset_confirm.email',
                name=user.forenames,
                confirmurl=flask.url_for(
                    'front.reset_password',
                    user_id=user.object_id,
                    secret_key=user.secret_key,
                    _external=True
                )
            )

        flask.flash(
            (
                'An email has been sent to {0} with detailing what to do '
                'next. Please check your email (including your spam folder) '
                'and follow the instructions given'
            ).format(
                flask.request.form['email']
            ),
            'info'
        )

        return flask.redirect(flask.url_for('front.home'))
    else:
        return flask.render_template('front/password_reset.html')

@FRONT.route('/resetpassword/<int:user_id>/<secret_key>',
             methods=['GET', 'POST'])
def reset_password(user_id, secret_key):
    """Complete the password reset process.

    To reset their password, the user is sent an email with a link to this view.
    Upon clicking it, they are presented with a form to define a new password,
    which is saved when the form is submitted (to this view)
    """
    user = models.User.get_by_id(user_id)

    if user is None or user.secret_key != secret_key:
        if user is not None:
            user.secret_key = None
            user.secret_key_expiry = None

            DB.session.commit()

        flask.flash('Could not complete password reset. Please try again',
                    'error')

        return flask.redirect(flask.url_for('front.home'))

    if flask.request.method == 'POST':
        if flask.request.form['password'] != flask.request.form['confirm']:
            user.secret_key = util.generate_key(64)
            user.secret_key_expiry = (datetime.datetime.utcnow() +
                                      datetime.timedelta(minutes=5))

            DB.session.commit()

            flask.flash('Passwords do not match, please try again', 'warning')

            return flask.redirect(
                flask.url_for(
                    'front.reset_password',
                    user_id=user.object_id,
                    secret_key=user.secret_key
                )
            )
        else:
            user.set_password(flask.request.form['password'])

            user.secret_key = None
            user.secret_key_expiry = None

            DB.session.commit()

            APP.log_manager.log_event(
                'Completed password reset',
                [],
                user
            )

            flask.flash('Your password has been reset, please log in.',
                        'success')

            return flask.redirect(flask.url_for('front.home'))
    else:
        return flask.render_template(
            'front/reset_password.html',
            user_id=user_id,
            secret_key=secret_key
        )

@FRONT.route('/destroyaccount/<int:user_id>/<secret_key>')
def destroy_account(user_id, secret_key):
    """Destroy an unverified account.

    If a user is unverified (and therefore has never been able to log in), we
    allow their account to be destroyed. This is useful if somebody tries to
    register with an email address that isn't theirs, where the actual owner of
    the email address can trigger the account's distruction.

    If a user is verified, it gets a little too complicated to destroy their
    account (what happens to any tickets they own?)
    """
    user = models.User.get_by_id(user_id)

    if user is not None and user.secret_key == secret_key:
        if not user.is_verified:
            for entry in user.events:
                entry.action = (
                    entry.action +
                    ' (destroyed user with email address {0})'.format(
                        user.email
                    )
                )
                entry.user = None

            DB.session.delete(user)
            DB.session.commit()

            APP.log_manager.log_event(
                'Deleted account with email address {0}'.format(
                    user.email
                )
            )

            flask.flash('The account has been deleted.', 'info')
        else:
            APP.log_manager.log_event(
                'Attempted deletion of verified account',
                [],
                user
            )

            flask.flash('Could not delete user account.', 'warning')
    else:
        flask.flash(
            (
                'Could not delete user account. Check that you have used the '
                'correct link'
            ),
            'warning'
        )

    return flask.redirect(flask.url_for('front.home'))

@FRONT.route('/logout')
@login.login_required
def logout():
    """Log out the currently logged in user.

    The system allows admins to impersonate other users; this view checks if the
    currently logged in user is being impersonated, and if so logs back in as
    the admin who is impersonating them.
    """
    if 'actor_id' in flask.session:
        APP.log_manager.log_event(
            'Finished impersonating user',
            [],
            login.current_user
        )

        actor = models.User.get_by_id(flask.session['actor_id'])

        flask.session.pop('actor_id', None)

        if actor:
            login.login_user(
                actor
            )

            return flask.redirect(flask.url_for('admin.admin_home'))

    APP.log_manager.log_event(
        'Logged Out',
        [],
        login.current_user
    )

    login.logout_user()
    return flask.redirect(flask.url_for('front.home'))

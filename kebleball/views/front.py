# coding: utf-8
"""Views related to users who aren't logged in."""

from datetime import datetime, timedelta

import flask
from flask.ext import login

from kebleball import app
from kebleball.helpers import generate_key
from kebleball.database import db
from kebleball.database import models

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
            u'Could not complete log in. Invalid email or password.',
            u'error'
        )
        return flask.redirect(flask.url_for('front.home'))

    if not user.verified:
        APP.log_manager.log_event(
            'Failed login attempt - not verified',
            [],
            user
        )
        flask.flash(
            u'Could not complete log in. Email address is not confirmed.',
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

    flask.flash(u'Logged in successfully.', 'success')
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

    valid = True
    flask.flashes = []

    if models.User.get_by_email(flask.request.form['email']) is not None:
        flask.flash(
            (
                u'That email address already has an associated account. '
                u'Use the links below to verify your email or reset your '
                u'password.'
            ),
            'error'
        )
        return flask.redirect(flask.url_for('front.home'))

    if (
            'password' not in flask.request.form or
            'confirm' not in flask.request.form or
            flask.request.form['password'] != flask.request.form['confirm']
    ):
        flask.flashes.append(u'Passwords do not match')
        valid = False

    if (
            'forenames' not in flask.request.form or
            flask.request.form['forenames'] == ''
    ):
        flask.flashes.append(u'First Name cannot be blank')
        valid = False

    if (
            'surname' not in flask.request.form or
            flask.request.form['surname'] == ''
    ):
        flask.flashes.append(u'Surname cannot be blank')
        valid = False

    if (
            'email' not in flask.request.form or
            flask.request.form['email'] == ''
    ):
        flask.flashes.append(u'Email cannot be blank')
        valid = False

    if (
            'password' not in flask.request.form or
            flask.request.form['password'] == ''
    ):
        flask.flashes.append(u'Password cannot be blank')
        valid = False
    elif len(flask.request.form['password']) < 8:
        flask.flashes.append(u'Password must be at least 8 characters long')
        valid = False

    if (
            'phone' not in flask.request.form or
            flask.request.form['phone'] == ''
    ):
        flask.flashes.append(u'Phone cannot be blank')
        valid = False

    if (
            'college' not in flask.request.form or
            flask.request.form['college'] == '---'
    ):
        flask.flashes.append(u'Please select a college')
        valid = False

    if (
            'affiliation' not in flask.request.form or
            flask.request.form['affiliation'] == '---'
    ):
        flask.flashes.append(u'Please select an affiliation')
        valid = False

    if not valid:
        flask.flash(
            (
                u'There were errors in your provided details. Please fix '
                u'these and try again'
            ),
            'error'
        )
        for msg in flask.flashes:
            flask.flash(msg, 'warning')

        return flask.render_template(
            'front/home.html',
            form=flask.request.form,
            colleges=models.College.query.all(),
            affiliations=models.Affiliation.query.all()
        )

    user = models.User(
        flask.request.form['email'],
        flask.request.form['password'],
        flask.request.form['forenames'],
        flask.request.form['surname'],
        flask.request.form['phone'],
        flask.request.form['college'],
        flask.request.form['affiliation']
    )

    DB.flask.session.add(user)
    DB.flask.session.commit()

    APP.log_manager.log_event(
        'Registered',
        [],
        user
    )

    APP.email_manager.send_template(
        flask.request.form['email'],
        'Confirm your Email Address',
        'emailConfirm.email',
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

    flask.flash(u'Your user account has been registered', 'success')
    flask.flash(
        (
            u'Before you can log in, you must confirm your email address. '
            u'Please check your email for further instructions. If the message '
            u'does not arrive, please check your spam/junk mail folder.'
        ),
        'info'
    )

    user.maybe_verify_affiliation()

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

        DB.flask.session.commit()

        APP.log_manager.log_event(
            'Confirmed email',
            [],
            user
        )

        flask.flash(u'Your email address has been verified. You can now log in',
                    u'info')
    else:
        flask.flash(
            (
                u'Could not confirm email address. Check that you have used '
                u'the correct link'
            ),
            'warning'
        )

    return flask.redirect(flask.url_for('front.home'))

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
                'emailConfirmFail.email'
            )
        else:
            user.secret_key = generate_key(64)
            user.secret_key_expiry = None

            DB.flask.session.commit()

            APP.log_manager.log_event(
                'Requested email confirm',
                [],
                user
            )

            APP.email_manager.send_template(
                flask.request.form['email'],
                'Confirm your Email Address',
                'emailConfirm.email',
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
                u'An email has been sent to {0} with detailing what to do '
                u'next. Please check your email (including your spam folder) '
                u'and follow the instructions given'
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

            app.email_manager.send_template(
                flask.request.form['email'],
                'Attempted Account Access',
                'passwordResetFail.email'
            )
        else:
            user.secret_key = generate_key(64)
            user.secret_key_expiry = (
                datetime.utcnow() +
                timedelta(minutes=30)
            )

            DB.flask.session.commit()

            APP.log_manager.log_event(
                'Started password reset',
                [],
                user
            )

            APP.email_manager.send_template(
                flask.request.form['email'],
                'Confirm Password Reset',
                'passwordResetConfirm.email',
                confirmurl=flask.url_for(
                    'front.reset_password',
                    user_id=user.object_id,
                    secret_key=user.secret_key,
                    _external=True
                )
            )

        flask.flash(
            (
                u'An email has been sent to {0} with detailing what to do '
                u'next. Please check your email (including your spam folder) '
                u'and follow the instructions given'
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
        user.secret_key = None
        user.secret_key_expiry = None

        DB.flask.session.commit()

        flask.flash(u'Could not complete password reset. Please try again',
                    u'error')

        return flask.redirect(flask.url_for('front.home'))

    if flask.request.method == 'POST':
        if flask.request.form['password'] != flask.request.form['confirm']:
            user.secret_key = generate_key(64)
            user.secret_key_expiry = datetime.utcnow() + timedelta(minutes=5)

            DB.flask.session.commit()

            flask.flash(u'Passwords do not match, please try again', 'warning')

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

            DB.flask.session.commit()

            APP.log_manager.log_event(
                'Completed password reset',
                [],
                user
            )

            flask.flash(u'Your password has been reset, please log in.',
                        u'success')

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
        if not user.is_verified():
            for entry in user.events:
                entry.action = (
                    entry.action +
                    ' (destroyed user with email address {0})'.format(
                        user.email
                    )
                )
                entry.user = None

            DB.flask.session.delete(user)
            DB.flask.session.commit()

            APP.log_manager.log_event(
                'Deleted account with email address {0}'.format(
                    user.email
                )
            )

            flask.flash(u'The account has been deleted.', 'info')
        else:
            APP.log_manager.log_event(
                'Attempted deletion of verified account',
                [],
                user
            )

            flask.flash(u'Could not delete user account.', 'warning')
    else:
        flask.flash(
            (
                u'Could not delete user account. Check that you have used the '
                u'correct link'
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

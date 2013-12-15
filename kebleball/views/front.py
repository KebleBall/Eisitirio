from flask import Blueprint, render_template, request, redirect, url_for

from flask.ext.login import login_user, logout_user, login_required

from kebleball.app import app
from kebleball.helpers.logger import Logger
from kebleball.helpers import generate_key
from kebleball.database import db
from kebleball.database.user import User

from datetime import datetime, timedelta

logger = Logger(app)

log = logger.log_front

front = Blueprint('front', __name__)

@front.route('/home')
def home():
    return render_template('front/home.html')

@front.route('/login', methods=['POST'])
def login():
    user = User.get_by_email(request.form['email'])

    if not user or not user.checkPassword(request.form['password']):
        flash(u'Could not complete log in. Invalid email or password.', 'error')
        return redirect(url_for('home'))

    if not user.verified:
        flash(
            u'Could not complete log in. Email address is not confirmed.',
            'warning'
        )
        return redirect(url_for('home'))

    login_user(user)
    flash(u'Logged in successfully.', 'success')
    return redirect(request.form["next"] or url_for("dashboard.dashboard"))


@front.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        valid = True

        if User.get_by_email(request.form['email']) is not None:
            flash(
                (
                    u'That email address already has an associated account. '
                    u'Use the links below to verify your email or reset your '
                    u'password.'
                ),
                'error'
            )
            return render_template('home.html')

        if request.form['password'] != request.form['confirm']:
            flash(u'Passwords do not match', 'warning')
            valid = False

        # [todo] - Finish register off

@front.route('/terms')
def terms():
    return render_template('front/terms.html')

@front.route('/passwordreset', methods=['GET','POST'])
def passwordReset():
    if request.method == 'POST':
        user = User.get_by_email(request.form['email'])

        if not user:
            # [todo] - Send 'Attempted account entry' email
        else:
            # [todo] - Send 'Confirm identity' email

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

        return redirect(url_for('home'))
    else:
        return render_template('passwordReset.html')

@front.route('/emailconfirm', methods=['GET','POST'])
def emailConfirm():
    if request.method == 'POST':
        user = User.get_by_email(request.form['email'])

        if not user:
            # [todo] - Send 'Attempted account entry' email
        else:
            # [todo] - Send 'Confirm identity' email

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

        return redirect(url_for('home'))
    else:
        return render_template('emailConfirm.html')

@front.route('/resetpassword/<int:userID>/<secretkey>', methods=['GET', 'POST'])
def resetPassword(userID, secretkey):
    user = User.get_by_id(userID)

    if user is None or user.secretkey != secretkey:
        user.secretkey = None
        user.secretkeyexpiry = None
        db.session.commit()
        flash(u'Could not complete password reset. Please try again','error')
        return redirect(url_for('home'))

    if request.method == 'POST':
        if request.form['password'] != request.form['confirm']:
            user.secretkey = generate_key(64)
            user.secretkeyexpiry = datetime.utcnow() + timedelta(minutes=5)
            db.session.commit()
            flash(u'Passwords do not match, please try again', 'warning')
            return render_template('front/resetPassword.html', user=user)
        else:
            user.setPassword(request.form['password'])
            user.secretkey = None
            user.secretkeyexpiry = None
            db.session.commit()
            flash(u'Your password has been reset, please log in.','success')
            return redirect(url_for('home'))
    else:
        flash(u'Identity confirmed, please enter a new password','info')
        return render_template('front/resetPassword.html', user=user)



@front.route('/confirmemail/<int:userID>/<secretkey>')
def confirmEmail(userID, secretkey):
    user = User.get_by_id(userID)

    if user is not None and user.secretkey == secretkey:
        user.secretkey = None
        user.verified = True
        db.session.commit()
        flash(u'Your email address has been verified. You can now log in','info')
    else:
        flash(u'Could not confirm email address. Check that you have used the correct link','warning')

    return redirect(url_for('home'))

@front.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
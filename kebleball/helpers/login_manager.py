# coding: utf-8
#
from functools import wraps

from flask import current_app
from flask import flash
from flask import redirect
from flask import url_for
from flask.ext import login as flask_login

from kebleball.database import db
from kebleball.database import user

LOGIN_MANAGER = flask_login.LoginManager()
LOGIN_MANAGER.login_message_category = 'message info'

@LOGIN_MANAGER.user_loader
def load_user(user_id):
    if current_app.config['MAINTENANCE_MODE']:
        return LOGIN_MANAGER.anonymous_user
    else:
        return user.User.get_by_id(user_id)

LOGIN_MANAGER.login_view = "front.home"
LOGIN_MANAGER.session_protection = "strong"

# Crude duplicate of the Flask-Login login_required decorator
def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_app.login_manager._login_disabled:
            return func(*args, **kwargs)
        elif not flask_login.current_user.is_authenticated():
            return current_app.login_manager.unauthorized()
        elif not flask_login.current_user.is_admin():
            flash(
                u'You are not permitted to perform that action',
                'error'
            )
            return redirect(url_for('dashboard.dashboard_home'))
        return func(*args, **kwargs)
    return decorated_view

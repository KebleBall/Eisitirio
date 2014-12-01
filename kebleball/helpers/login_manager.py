# coding: utf-8
from functools import wraps

from flask import redirect, url_for, flash, current_app
from flask.ext.login import LoginManager, current_user
from kebleball.database.user import User

loginManager = LoginManager()
loginManager.login_message_category = 'message info'

@loginManager.user_loader
def load_user(user_id):
    if current_app.config['MAINTENANCE_MODE']:
        return loginManager.anonymous_user
    else:
        return User.get_by_id(user_id)

loginManager.login_view = "front.home"

loginManager.session_protection = "strong"

# Crude duplicate of the Flask-Login login_required decorator
def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_app.login_manager._login_disabled:
            return func(*args, **kwargs)
        elif not current_user.is_authenticated():
            return current_app.login_manager.unauthorized()
        elif not current_user.isAdmin():
            flash(
                u'You are not permitted to perform that action',
                'error'
            )
            return redirect(url_for('dashboard.dashboardHome'))
        return func(*args, **kwargs)
    return decorated_view

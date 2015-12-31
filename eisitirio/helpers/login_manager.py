# coding: utf-8
"""Set up flask.ext.login for our own purposes."""

from __future__ import unicode_literals

import functools

from flask.ext import login
import flask

from eisitirio.database import models

LOGIN_MANAGER = login.LoginManager()
LOGIN_MANAGER.login_message_category = 'message info'

@LOGIN_MANAGER.user_loader
def load_user(user_id):
    """Function used by flask.ext.login to load a user object given an ID.

    Checks if the app is in maintenance mode (and returns an anonymous user if
    so), and otherwise simply loads the user object from the database.
    """
    if flask.current_app.config['MAINTENANCE_MODE']:
        return LOGIN_MANAGER.anonymous_user
    else:
        return models.User.get_by_id(user_id)

LOGIN_MANAGER.login_view = 'front.home'
LOGIN_MANAGER.session_protection = 'strong'

def admin_required(func):
    """View decorator to enforce admin privileges for the view.

    Checks if the user is an admin, and otherwise flashes an error message and
    redirects them to the dashboard. Must be used inside a login_required
    decorator.
    """

    @functools.wraps(func)
    def decorated_view(*args, **kwargs):
        if not login.current_user.is_admin:
            flask.flash(
                'You are not permitted to perform that action',
                'error'
            )

            return flask.redirect(flask.url_for('dashboard.dashboard_home'))
        else:
            return func(*args, **kwargs)

    return decorated_view

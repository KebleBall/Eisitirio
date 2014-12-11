# coding: utf-8
"""Body of the system to glue all the components together."""

import os

from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.ext import login as flask_login
from flask.ext import markdown as flask_markdown
from jinja2 import Markup
from werkzeug.exceptions import NotFound

from kebleball import app
from kebleball import views
from kebleball.helpers import log_manager
from kebleball.helpers import login_manager
from kebleball.helpers import email_manager

APP = app.APP

@APP.before_request
def check_for_maintenance():
    """Check whether the app is in maintenance mode.

    Checks for the existence of a maintenance file, and drops the app into
    maintenance mode displaying an information page only.

    Created as early as possible to ensure it is called before
    loginManager.login_user
    """
    if os.path.exists('/var/www/flask_kebleball/.maintenance'):
        APP.config['MAINTENANCE_MODE'] = True
        if (
                'maintenance' not in request.path and
                'static' not in request.path
        ):
            return redirect(url_for('maintenance'))

log_manager.LogManager(APP)
email_manager.EmailManager(APP)
login_manager.LOGIN_MANAGER.init_app(APP)
flask_markdown.Markdown(APP)

LOG = APP.log_manager.log_main

APP.register_blueprint(views.ADMIN)
APP.register_blueprint(views.AJAX)
APP.register_blueprint(views.DASHBOARD)
APP.register_blueprint(views.FRONT)
APP.register_blueprint(views.PURCHASE)
APP.register_blueprint(views.RESALE)

@APP.route('/')
def router():
    """Redirect the user to the appropriate homepage."""
    if not flask_login.current_user.is_anonymous():
        return redirect(url_for('dashboard.dashboard_home'))
    else:
        return redirect(url_for('front.home'))

@APP.route('/maintenance')
def maintenance():
    """Display the Server Maintenance page."""
    return render_template('maintenance.html'), 503

@APP.errorhandler(NotFound)
@APP.errorhandler(404)
def error_404(_):
    """Display the 404 Page"""
    LOG(
        'error',
        '404 not found for URL {0}, referrer {1}'.format(
            request.url,
            request.referrer
        )
    )
    return render_template('404.html'), 404

def server_error(code, error):
    """Generic handler for displaying Server Error pages."""
    LOG(
        'error',
        '{0} server error for URL {1}, error {2}'.format(
            code,
            request.url,
            error
        )
    )
    return render_template('500.html'), code

@APP.errorhandler(Exception)
@APP.errorhandler(500)
def error_500(error):
    """Display a 500 error page."""
    return server_error(500, error)


@APP.errorhandler(405)
def error_405(error):
    """Display a 405 error page."""
    return server_error(405, error)


@APP.errorhandler(400)
def error_400(error):
    """Display a 400 error page."""
    return server_error(400, error)

@APP.context_processor
def context_processor():
    """Add a number of utilities to the rendering engine."""
    def get_all(query):
        """Wrapper to transform a query object into a set of results."""
        return query.all()

    def get_ord(datetime):
        """Get the appropriate ordinal for a number."""
        daymod = datetime.day % 10
        if daymod == 1:
            return 'st'
        elif daymod == 2:
            return 'nd'
        elif daymod == 3:
            return 'rd'
        else:
            return 'th'

    def raise_exception():
        """Raise an exception for easy access to template debugger."""
        raise Exception

    def form_value(form, field, default=None):
        """Quick way of writing an input element's value attribute."""
        if field in form:
            return Markup('value="{0}" '.format(form[field]))
        elif default is not None:
            return Markup('value="{0}" '.format(default))
        else:
            return ''

    def form_selected(form, field, value):
        """Quick way of writing an input element's selected attribute."""
        if field in form and form[field] == str(value):
            return Markup('selected="selected" ')
        else:
            return ''

    def form_checked(form, field, value):
        """Quick way of writing an input element's checked attribute."""
        if field in form and form[field] == str(value):
            return Markup('checked="checked" ')
        else:
            return ''

    return dict(
        get_all=get_all,
        get_ord=get_ord,
        raise_exception=raise_exception,
        form_value=form_value,
        form_selected=form_selected,
        form_checked=form_checked,
        template_config={
            key: APP.config[key]
            for key in APP.config['TEMPLATE_CONFIG_KEYS']
        }
    )

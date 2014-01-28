# coding: utf-8
from flask import url_for, redirect, render_template, request
from jinja2 import Markup

from .app import app

# Put here so that it updates config before loginManager.login_user gets called
@app.before_request
def check_for_maintenance():
    if os.path.exists('/var/www/flask_kebleball/.maintenance'):
        app.config['MAINTENANCE_MODE'] = True
        if (
            'maintenance' not in request.path and
            'static' not in request.path
        ):
            return redirect(url_for('maintenance'))

from kebleball.helpers.log_manager import LogManager
from kebleball.helpers.login_manager import loginManager
from kebleball.helpers.email_manager import EmailManager
from flask.ext.markdown import Markdown

log_manager = LogManager(app)
app.log_manager = log_manager

email_manager = EmailManager(app)
app.email_manager = email_manager

loginManager.init_app(app)

Markdown(app)

log = app.log_manager.log_main

from flask.ext.login import current_user
from .views import *

import os

app.register_blueprint(admin.admin)
app.register_blueprint(ajax.ajax)
app.register_blueprint(dashboard.dashboard)
app.register_blueprint(front.front)
app.register_blueprint(purchase.purchase)
app.register_blueprint(resale.resale)

@app.route('/')
def router():
    if not current_user.is_anonymous():
        return redirect(url_for('dashboard.dashboardHome'))
    else:
        return redirect(url_for('front.home'))

@app.route('/environment')
def environment():
    return (
        app.config['ENVIRONMENT'] +
        " - " +
        str(os.environ)
    )

@app.route('/maintenance')
def maintenance():
    return render_template('maintenance.html'), 503

@app.errorhandler(404)
def error404(e):
    log(
        'error',
        '404 not found for URL {0}, referrer {1}'.format(
            request.url,
            request.referrer
        )
    )
    return render_template('404.html'), 404

#@app.errorhandler(Exception)
@app.errorhandler(500)
@app.errorhandler(405)
def error500(e):
    log(
        'error',
        '500 server error for URL {0}, error {1}'.format(
            request.url,
            e
        )
    )
    return render_template('500.html')

@app.context_processor
def utility_processor():
    def get_all(query):
        return query.all()

    def get_ord(datetime):
        daymod = int(datetime.strftime('%d')) % 10
        if daymod == 1:
            return 'st'
        elif daymod == 2:
            return 'nd'
        elif daymod == 3:
            return 'rd'
        else:
            return 'th'

    def raise_exception():
        raise Exception

    def form_value(form, field, default=None):
        if field in form:
            return Markup('value="{0}" '.format(form[field]))
        elif default is not None:
            return Markup('value="{0}" '.format(default))
        else:
            return ''

    def form_selected(form, field, value):
        if field in form and form[field] == str(value):
            return Markup('selected="selected" ')
        else:
            return ''

    def form_checked(form, field, value):
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
        template_config={key: app.config[key] for key in app.config['TEMPLATE_CONFIG_KEYS']}
    )

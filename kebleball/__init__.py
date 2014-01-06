from flask import url_for, redirect, render_template, request

from .app import app
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

    return dict(
        get_all=get_all,
        get_ord=get_ord,
        template_config={key: app.config[key] for key in app.config['TEMPLATE_CONFIG_KEYS']}
    )

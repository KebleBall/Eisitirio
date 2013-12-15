from flask import url_for, redirect, render_template, request

from .app import app

from flask.ext.login import current_user
from .views import *
from kebleball.helpers.logger import Logger
from kebleball.helpers.login_manager import loginManager

logger = Logger(app)

log = logger.log_main

app.register_blueprint(admin.admin)
app.register_blueprint(ajax.ajax)
app.register_blueprint(dashboard.dashboard)
app.register_blueprint(front.front)
app.register_blueprint(purchase.purchase)
app.register_blueprint(resale.resale)

loginManager.init_app(app)

@app.route('/')
def router():
    if not current_user.is_anonymous():
        return redirect(url_for('dashboard.dashboardHome'))
    else:
        return redirect(url_for('front.home'))

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

@app.errorhandler(Exception)
@app.errorhandler(500)
def error500(e):
    log(
        'error',
        '500 server error for URL {0}'.format(
            request.url
        )
    )
    return render_template('500.html')

@app.context_processor
def utility_processor():
    def get_all(query):
        return query.all()
    return dict(
        get_all=get_all,
        current_user=current_user
    )

from flask import Blueprint
from flask.ext.login import login_required, fresh_login_required

from kebleball.app import app

log = app.log_manager.log_dashboard

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard')
@login_required
def dashboardHome():
    # [todo] - Add dashboardHome
    raise NotImplementedError('dashboardHome')

@dashboard.route('/dashboard/profile')
@fresh_login_required
def profile():
    # [todo] - Add profile
    raise NotImplementedError('profile')

@dashboard.route('/dashboard/resell')
@fresh_login_required
def resell():
    # [todo] - Add resell
    raise NotImplementedError('resell')
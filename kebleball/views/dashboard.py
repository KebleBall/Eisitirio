from flask import Blueprint, render_template
from flask.ext.login import login_required, fresh_login_required

from kebleball.app import app

log = app.log_manager.log_dashboard

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard')
@login_required
def dashboardHome():
    return render_template('dashboard/dashboardHome.html')

@dashboard.route('/dashboard/profile')
@fresh_login_required
def profile(methods=['GET','POST']):
    # [todo] - Add profile
    raise NotImplementedError('profile')

@dashboard.route('/dashboard/announcement/<int:announcementID')
@login_required
def announcement(announcementID):
    # [todo] - Add announcement
    raise NotImplementedError('announcement')
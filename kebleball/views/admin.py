from flask import Blueprint
from flask.ext.login import login_required

from kebleball.app import app

log = app.log_manager.log_admin

admin = Blueprint('admin', __name__)

@admin.route('/admin')
@login_required
def adminHome():
    # [todo] - Add adminHome
    raise NotImplementedError('adminHome')

@admin.route('/admin/statistics')
@login_required
def statistics():
    # [todo] - Add statistics
    raise NotImplementedError('statistics')

@admin.route('/admin/search-database')
@login_required
def searchDatabase():
    # [todo] - Add searchDatabase
    raise NotImplementedError('searchDatabase')

@admin.route('/admin/announcements')
@login_required
def announcements():
    # [todo] - Add announcements
    raise NotImplementedError('announcements')

@admin.route('/admin/vouchers')
@login_required
def vouchers():
    # [todo] - Add vouchers
    raise NotImplementedError('vouchers')

@admin.route('/admin/graphs/sales')
@login_required
def graphSales():
    # [todo] - Add graphSales
    raise NotImplementedError('graphSales')

@admin.route('/admin/graphs/colleges')
@login_required
def graphColleges():
    # [todo] - Add graphColleges
    raise NotImplementedError('graphColleges')

@admin.route('/admin/graphs/payments')
@login_required
def graphPayments():
    # [todo] - Add graphPayments
    raise NotImplementedError('graphPayments')

@admin.route('/admin/data/sales')
@login_required
def dataSales():
    # [todo] - Add dataSales
    raise NotImplementedError('dataSales')

@admin.route('/admin/data/colleges')
@login_required
def dataColleges():
    # [todo] - Add dataColleges
    raise NotImplementedError('dataColleges')

@admin.route('/admin/data/payments')
@login_required
def dataPayments():
    # [todo] - Add dataPayments
    raise NotImplementedError('dataPayments')
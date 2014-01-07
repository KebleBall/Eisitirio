# coding: utf-8
from flask import Blueprint

from kebleball.app import app
from kebleball.helpers.login_manager import admin_required

log = app.log_manager.log_admin

admin = Blueprint('admin', __name__)

@admin.route('/admin')
@admin_required
def adminHome():
    # [todo] - Add adminHome
    raise NotImplementedError('adminHome')

@admin.route('/admin/statistics')
@admin_required
def statistics():
    # [todo] - Add statistics
    raise NotImplementedError('statistics')

@admin.route('/admin/search-database')
@admin_required
def searchDatabase():
    # [todo] - Add searchDatabase
    raise NotImplementedError('searchDatabase')

@admin.route('/admin/announcements')
@admin_required
def announcements():
    # [todo] - Add announcements
    raise NotImplementedError('announcements')

@admin.route('/admin/vouchers')
@admin_required
def vouchers():
    # [todo] - Add vouchers
    raise NotImplementedError('vouchers')

@admin.route('/admin/graphs/sales')
@admin_required
def graphSales():
    # [todo] - Add graphSales
    raise NotImplementedError('graphSales')

@admin.route('/admin/graphs/colleges')
@admin_required
def graphColleges():
    # [todo] - Add graphColleges
    raise NotImplementedError('graphColleges')

@admin.route('/admin/graphs/payments')
@admin_required
def graphPayments():
    # [todo] - Add graphPayments
    raise NotImplementedError('graphPayments')

@admin.route('/admin/data/sales')
@admin_required
def dataSales():
    # [todo] - Add dataSales
    raise NotImplementedError('dataSales')

@admin.route('/admin/data/colleges')
@admin_required
def dataColleges():
    # [todo] - Add dataColleges
    raise NotImplementedError('dataColleges')

@admin.route('/admin/data/payments')
@admin_required
def dataPayments():
    # [todo] - Add dataPayments
    raise NotImplementedError('dataPayments')
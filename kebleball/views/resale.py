from flask import Blueprint
from flask.ext.login import login_required

from kebleball.app import app

log = app.log_manager.log_resale

resale = Blueprint('resale', __name__)

@resale.route('/resale/<int:ticket>')
@login_required
def resaleHome(ticket):
    # [todo] - Add resaleHome
    raise NotImplementedError('resaleHome')

@resale.route('/resale/start/<int:ticket>')
@login_required
def resaleStart(ticket):
    # [todo] - Add resaleStart
    raise NotImplementedError('resaleStart')

@resale.route('/resale/confirm/<int:ticket>/<key>')
@login_required
def resaleConfirm(ticket, key):
    # [todo] - Add resaleConfirm
    raise NotImplementedError('resaleConfirm')

@resale.route('/resale/complete/<int:ticket>/<key>')
@login_required
def resaleComplete(ticket, key):
    # [todo] - Add resaleComplete
    raise NotImplementedError('resaleComplete')

@resale.route('/resale/cancel/<int:ticket>/<key>')
@login_required
def resaleCancel(ticket, key):
    # [todo] - Add resaleCancel
    raise NotImplementedError('resaleCancel')
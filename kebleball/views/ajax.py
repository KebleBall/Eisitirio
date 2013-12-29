from flask import Blueprint

from kebleball.app import app

log = app.log_manager.log_ajax

ajax = Blueprint('ajax', __name__)

@ajax.route('/ajax/validate/voucher')
def validateVoucher():
    # [todo] - Add validateVoucher
    raise NotImplementedError('validateVoucher')

@ajax.route('/ajax/validate/referrer')
def validateReferrer():
    # [todo] - Add validateReferrer
    raise NotImplementedError('validateReferrer')
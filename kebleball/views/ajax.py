from flask import Blueprint

ajax = Blueprint('ajax', __name__)

@ajax.route('/ajax/validate/email')
def validateEmail():
    # [todo] - Add validateEmail
    raise NotImplementedError('validateEmail')

@ajax.route('/ajax/validate/voucher')
def validateVoucher():
    # [todo] - Add validateVoucher
    raise NotImplementedError('validateVoucher')
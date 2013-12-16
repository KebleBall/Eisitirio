from flask import Blueprint
from flask.ext.login import login_required

from kebleball.app import app

log = app.log_manager.log_purchase

purchase = Blueprint('purchase', __name__)

@purchase.route('/purchase')
@login_required
def purchaseHome():
    # [todo] - Add purchaseHome
    raise NotImplementedError('purchaseHome')

@purchase.route('/purchase/eway-callback')
@login_required
def ewayCallback():
    # [todo] - Add ewayCallback
    raise NotImplementedError('ewayCallback')

@purchase.route('/purchase/battels-confirm')
@login_required
def battelsConfirm():
    # [todo] - Add battelsConfirm
    raise NotImplementedError('battelsConfirm')

@purchase.route('/purchase/cash-cheque-confirm')
@login_required
def cashChequeConfirm():
    # [todo] - Add cashChequeConfirm
    raise NotImplementedError('cashChequeConfirm')
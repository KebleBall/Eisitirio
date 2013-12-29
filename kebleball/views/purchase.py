from flask import Blueprint, request
from flask.ext.login import login_required, fresh_login_required

from kebleball.app import app

log = app.log_manager.log_purchase
log_entry = app.log_manager.log_entry

purchase = Blueprint('purchase', __name__)

@purchase.route('/purchase')
@login_required
def purchaseHome(methods=['GET','POST']):
    if request.method == 'POST':
        pass
    else:
        return render_template('purchase/purchaseHome.html')

@purchase.route('/purchase/change-method')
@login_required
def changeMethod():
    # [todo] - Add changeMethod
    raise NotImplementedError('changeMethod')

@purchase.route('/purchase/card-confirm')
@login_required
def cardConfirm():
    # [todo] - Add cardConfirm
    raise NotImplementedError('cardConfirm')

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

@purchase.route('/purchase/resell')
@fresh_login_required
def resell():
    # [todo] - Add resell
    raise NotImplementedError('resell')

@purchase.route('/purchase/cancel')
@fresh_login_required
def cancel():
    # [todo] - Add cancel
    raise NotImplementedError('cancel')
from flask import Blueprint, Response, request

from kebleball.app import app
from kebleball.database.voucher import Voucher
from kebleball.database.user import User

from flask.ext.login import current_user

from datetime import datetime
import json

log = app.log_manager.log_ajax

ajax = Blueprint('ajax', __name__)

@ajax.route('/ajax/validate/voucher', methods=['POST'])
def validateVoucher():
    voucher = Voucher.query.filter(Voucher.code==request.form['code']).first()

    if not voucher:
        result = {
            'class': 'message-box error',
            'message': "<p>Sorry, that voucher code wasn't recognised. Please ensure you have entered it correctly.</p>"
        }
    else:
        if voucher.singleuse and voucher.used:
            result = {
                'class': 'message-box error',
                'message': "<p>Sorry, that voucher code has already been used.</p>"
            }
        elif voucher.expires is not None and voucher.expires < datetime.utcnow():
            result = {
                'class': 'message-box error',
                'message': "<p>Sorry, that voucher code has expired.</p>"
            }
        else:
            if voucher.discounttype == 'Fixed Price':
                message = "<p>This voucher gives a fixed price of &pound;{0:.2f} for ".format(
                    (voucher.discountvalue / 100.0)
                )
            elif voucher.discounttype == 'Fixed Discount':
                message = "<p>This voucher gives a fixed &pound;{0:.2f} discount off ".format(
                    (voucher.discountvalue / 100.0)
                )
            else:
                message = "<p>This voucher gives a {0:d}% discount off ".format(
                    voucher.discountvalue
                )

            if voucher.appliesto == "Ticket":
                message = message + "one ticket.</p>"
            else:
                message = message + "all tickets purchased in one transaction.</p>"

            result = {
                'class': 'message-box success',
                'message': message
            }

    return Response(json.dumps(result), mimetype="text/json")

@ajax.route('/ajax/validate/referrer', methods=['POST'])
def validateReferrer():
    user = User.get_by_email(request.form['email'])

    if user:
        if user == current_user:
            result = {
                'class': 'message-box error',
                'message': "<p>You can't credit yourself for your own order!</p>"
            }
        else:
            result = {
                'class': 'message-box success',
                'message': '<p>{0} will be credited for your order.</p>'.format(user.name)
            }
    else:
        result = {
            'class': 'message-box warning',
            'message': (
                '<p>No user with that email address was found, have you '
                'entered it correctly? The person who referred you must have '
                'an account before they can be given credit for your order. '
                'You can still continue with your order without giving credit.'
                '</p>'
            )
        }

    return Response(json.dumps(result), mimetype="text/json")
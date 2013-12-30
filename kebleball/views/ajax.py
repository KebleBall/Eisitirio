from flask import Blueprint, Response, request

from kebleball.app import app
from kebleball.helpers.validators import validateVoucher, validateReferrer

from flask.ext.login import current_user

import json

log = app.log_manager.log_ajax

ajax = Blueprint('ajax', __name__)

@ajax.route('/ajax/validate/voucher', methods=['POST'])
def ajaxValidateVoucher():
    (result, response, voucher) = validateVoucher(request.form['code'])

    response['class'] = 'message-box ' + response['class']
    response['message'] = '<p>' + response['message'] + '</p>'

    return Response(json.dumps(response), mimetype="text/json")

@ajax.route('/ajax/validate/referrer', methods=['POST'])
def ajaxValidateReferrer():
    (result, response, referrer) = validateReferrer(request.form['email'], current_user)

    response['class'] = 'message-box ' + response['class']
    response['message'] = '<p>' + response['message'] + '</p>'

    return Response(json.dumps(response), mimetype="text/json")
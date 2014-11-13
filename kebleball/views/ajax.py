# coding: utf-8
from flask import Blueprint, Response, request

from kebleball.app import app
from kebleball.helpers.validators import validateVoucher, validateReferrer, validateResaleEmail
from kebleball.database import db
from kebleball.database.ticket import Ticket

from flask.ext.login import current_user

import json

log = app.log_manager.log_ajax

AJAX = Blueprint('ajax', __name__)

@AJAX.route('/ajax/validate/voucher', methods=['POST'])
def ajaxValidateVoucher():
    (result, response, voucher) = validateVoucher(request.form['code'])

    response['class'] = 'message-box ' + response['class']
    response['message'] = '<p>' + response['message'] + '</p>'

    return Response(json.dumps(response), mimetype="text/json")

@AJAX.route('/ajax/validate/referrer', methods=['POST'])
def ajaxValidateReferrer():
    (result, response, referrer) = validateReferrer(request.form['email'], current_user)

    response['class'] = 'message-box ' + response['class']
    response['message'] = '<p>' + response['message'] + '</p>'

    return Response(json.dumps(response), mimetype="text/json")

@AJAX.route('/ajax/validate/resale-email', methods=['POST'])
def ajaxValidateResaleEmail():
    (result, response, buyer) = validateResaleEmail(request.form['email'], current_user)

    response['class'] = 'message-box ' + response['class']
    response['message'] = '<p>' + response['message'] + '</p>'

    return Response(json.dumps(response), mimetype="text/json")

@AJAX.route('/ajax/change/ticket/<int:id>/name', methods=['POST'])
def ajaxChangeTicketName(id):
    ticket = Ticket.get_by_id(id)

    if ticket and request.form['name'] != '':
        ticket.name = request.form['name']

        db.session.commit()
        return Response(json.dumps(True), mimetype="text/json")
    else:
        return Response(json.dumps(False), mimetype="text/json")

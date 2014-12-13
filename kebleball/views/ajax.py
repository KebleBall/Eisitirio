# coding: utf-8

import json

from flask import Blueprint, Response, request
from flask.ext import login

from kebleball.helpers import validators
from kebleball.database import db
from kebleball.database import ticket

DB = db.DB
Ticket = ticket.Ticket

AJAX = Blueprint('ajax', __name__)

@AJAX.route('/ajax/validate/voucher', methods=['POST'])
def ajaxValidateVoucher():
    (result, response, voucher) = validators.validateVoucher(request.form['code'])

    response['class'] = 'message-box ' + response['class']
    response['message'] = '<p>' + response['message'] + '</p>'

    return Response(json.dumps(response), mimetype="text/json")

@AJAX.route('/ajax/validate/referrer', methods=['POST'])
def ajaxValidateReferrer():
    (result, response, referrer) = validators.validateReferrer(request.form['email'], login.current_user)

    response['class'] = 'message-box ' + response['class']
    response['message'] = '<p>' + response['message'] + '</p>'

    return Response(json.dumps(response), mimetype="text/json")

@AJAX.route('/ajax/validate/resale-email', methods=['POST'])
def ajaxValidateResaleEmail():
    (result, response, buyer) = validators.validateResaleEmail(request.form['email'], login.current_user)

    response['class'] = 'message-box ' + response['class']
    response['message'] = '<p>' + response['message'] + '</p>'

    return Response(json.dumps(response), mimetype="text/json")

@AJAX.route('/ajax/change/ticket/<int:id>/name', methods=['POST'])
def ajaxChangeTicketName(id):
    ticket = Ticket.get_by_id(id)

    if ticket and request.form['name'] != '':
        ticket.name = request.form['name']

        DB.session.commit()
        return Response(json.dumps(True), mimetype="text/json")
    else:
        return Response(json.dumps(False), mimetype="text/json")

# coding: utf-8
"""Views for performing tasks via AJAX requests."""

from __future__ import unicode_literals

import json

from flask import Blueprint, Response, request
from flask.ext import login

from kebleball.helpers import validators
from kebleball.database import db
from kebleball.database import models

DB = db.DB

AJAX = Blueprint('ajax', __name__)

@AJAX.route('/ajax/validate/voucher', methods=['POST'])
def validate_voucher():
    """Validate a discount voucher.

    Check the voucher exists and that it can be used.
    """
    (_, response, _) = validators.validate_voucher(request.form['code'])

    response['class'] = 'message-box ' + response['class']
    response['message'] = '<p>' + response['message'] + '</p>'

    return Response(json.dumps(response), mimetype='text/json')

@AJAX.route('/ajax/validate/referrer', methods=['POST'])
def validate_referrer():
    """Validate a referrer for purchasing tickets.

    Check the the referenced user has an account on the system.
    """
    (_, response, _) = validators.validate_referrer(request.form['email'],
                                                    login.current_user)

    response['class'] = 'message-box ' + response['class']
    response['message'] = '<p>' + response['message'] + '</p>'

    return Response(json.dumps(response), mimetype='text/json')

@AJAX.route('/ajax/validate/resale-email', methods=['POST'])
def validate_resale_email():
    """Validate a user for reselling tickets.

    Check the the referenced user has an account on the system.
    """
    (_, response, _) = validators.validate_resale_email(request.form['email'],
                                                        login.current_user)

    response['class'] = 'message-box ' + response['class']
    response['message'] = '<p>' + response['message'] + '</p>'

    return Response(json.dumps(response), mimetype='text/json')

@AJAX.route('/ajax/change/ticket/<int:object_id>/name', methods=['POST'])
def change_ticket_name(object_id):
    """Change the name on a ticket."""
    ticket = models.Ticket.get_by_id(object_id)

    if ticket and request.form['name'] != '':
        ticket.name = request.form['name']

        DB.session.commit()
        return Response(json.dumps(True), mimetype='text/json')
    else:
        return Response(json.dumps(False), mimetype='text/json')

# coding: utf-8
"""Views for performing tasks via AJAX requests."""

from __future__ import unicode_literals

import json

from flask.ext import login
import flask

from kebleball.database import db
from kebleball.database import models
from kebleball.helpers import validators

DB = db.DB

AJAX = flask.Blueprint('ajax', __name__)

@AJAX.route('/ajax/validate/voucher', methods=['POST'])
def validate_voucher():
    """Validate a discount voucher.

    Check the voucher exists and that it can be used.
    """
    (_, response, _) = validators.validate_voucher(flask.request.form['code'])

    response['class'] = 'message-box ' + response['class']
    response['message'] = '<p>' + response['message'] + '</p>'

    return flask.Response(json.dumps(response), mimetype='text/json')

@AJAX.route('/ajax/validate/referrer', methods=['POST'])
def validate_referrer():
    """Validate a referrer for purchasing tickets.

    Check the the referenced user has an account on the system.
    """
    (_, response, _) = validators.validate_referrer(flask.request.form['email'],
                                                    login.current_user)

    response['class'] = 'message-box ' + response['class']
    response['message'] = '<p>' + response['message'] + '</p>'

    return flask.Response(json.dumps(response), mimetype='text/json')

@AJAX.route('/ajax/validate/resale-email', methods=['POST'])
def validate_resale_email():
    """Validate a user for reselling tickets.

    Check the the referenced user has an account on the system.
    """
    (_, response, _) = validators.validate_resale_email(
        flask.request.form['email'],
        login.current_user
    )

    response['class'] = 'message-box ' + response['class']
    response['message'] = '<p>' + response['message'] + '</p>'

    return flask.Response(json.dumps(response), mimetype='text/json')

@AJAX.route('/ajax/change/ticket/<int:object_id>/name', methods=['POST'])
def change_ticket_name(object_id):
    """Change the name on a ticket."""
    ticket = models.Ticket.get_by_id(object_id)

    if ticket and flask.request.form['name'] != '':
        ticket.name = flask.request.form['name']

        DB.session.commit()
        return flask.Response(json.dumps(True), mimetype='text/json')
    else:
        return flask.Response(json.dumps(False), mimetype='text/json')

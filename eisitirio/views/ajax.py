# coding: utf-8
"""Views for performing tasks via AJAX requests."""

from __future__ import unicode_literals

import json

from flask.ext import login
import flask

from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import login_manager
from eisitirio.helpers import validators
from eisitirio.logic import collection_logic

DB = db.DB

AJAX = flask.Blueprint('ajax', __name__)

@AJAX.route('/ajax/validate/voucher', methods=['POST'])
@login.login_required
def validate_voucher():
    """Validate a discount voucher.

    Check the voucher exists and that it can be used.
    """
    (_, response, _) = validators.validate_voucher(flask.request.form['code'])

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

@AJAX.route('/ajax/ticket/<int:ticket_id>/collect', methods=['POST'])
@login.login_required
@login_manager.admin_required
def collect_ticket(ticket_id):
    """Mark a ticket as collected, and add a barcode.

    Performs the requisite logic to check the barcode submitted for a ticket,
    and marks the ticket as collected.
    """
    ticket = models.Ticket.get_by_id(ticket_id)

    if not ticket:
        response = {
            'success': False,
            'message': 'Could not load ticket.'
        }
    else:
        error = collection_logic.collect_ticket(
            ticket,
            flask.request.form['barcode']
        )

        if error is None:
            response = {
                'success': True,
            }
        else:
            response = {
                'success': False,
                'message': error
            }

    return flask.Response(json.dumps(response), mimetype='text/json')

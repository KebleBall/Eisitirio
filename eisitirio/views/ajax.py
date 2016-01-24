# coding: utf-8
"""Views for performing tasks via AJAX requests."""

from __future__ import unicode_literals

import json

from flask.ext import login
import flask

from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import validators

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

@AJAX.route('/ajax/change/ticket/<int:ticket_id>/name', methods=['POST'])
@login.login_required
def change_ticket_name(ticket_id):
    """Change the name on a ticket."""
    ticket = models.Ticket.get_by_id(ticket_id)

    if ticket and flask.request.form['name'] != '' and (
            ticket.owner == login.current_user or
            login.current_user.is_admin
    ):
        ticket.name = flask.request.form['name']

        DB.session.commit()
        return flask.Response(json.dumps(True), mimetype='text/json')
    else:
        return flask.Response(json.dumps(False), mimetype='text/json')

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

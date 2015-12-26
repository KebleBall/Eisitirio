# coding: utf-8
"""Views for performing tasks via AJAX requests."""

from __future__ import unicode_literals

import json

import flask

from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import validators

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

@AJAX.route('/ajax/change/ticket/<int:ticket_id>/name', methods=['POST'])
def change_ticket_name(ticket_id):
    """Change the name on a ticket."""
    ticket = models.Ticket.get_by_id(ticket_id)

    if ticket and flask.request.form['name'] != '':
        ticket.name = flask.request.form['name']

        DB.session.commit()
        return flask.Response(json.dumps(True), mimetype='text/json')
    else:
        return flask.Response(json.dumps(False), mimetype='text/json')

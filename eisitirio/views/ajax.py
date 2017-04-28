# coding: utf-8
"""Views for performing tasks via AJAX requests."""

from __future__ import unicode_literals

import json

import flask_login as login
# from flask.ext import login
import flask

from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import login_manager
from eisitirio.helpers import validators
from eisitirio.logic import collection_logic
from eisitirio.logic import sms_logic

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

@AJAX.route('/ajax/waiting/<int:entry_id>/reduce', methods=['POST'])
@login.login_required
def update_waiting(entry_id):
    """Change the number of tickets in a waiting list entry.

    Deletes the entry if the number is reduced to 0.
    """
    entry = models.Waiting.get_by_id(entry_id)

    if not entry:
        response = {
            'success': False,
            'message': 'Error: could not load entry.'
        }
    else:
        new_waiting_for = int(flask.request.form['waiting_for'])

        if new_waiting_for > entry.waiting_for:
            response = {
                'success': False,
                'message': (
                    'You cannot increase the quantity you are waiting for. '
                    'Please create a new waiting list entry if you would like '
                    'to wait for more tickets.'
                )
            }
        else:
            if new_waiting_for <= 0:
                DB.session.delete(entry)
            else:
                entry.waiting_for = new_waiting_for

            DB.session.commit()

            response = {
                'success': True,
            }

    return flask.Response(json.dumps(response), mimetype='text/json')

@AJAX.route('/ajax/user/phone/verify', methods=['GET'])
@login.login_required
def send_verify_code():
    """Send a verification code SMS to the user's phone."""

    return flask.Response(
        json.dumps(
            sms_logic.maybe_send_verification_code(login.current_user)
        ),
        mimetype='text/json'
    )

@AJAX.route('/ajax/user/phone/verify', methods=['POST'])
@login.login_required
def verify_phone():
    """Check the code sent via SMS to the user's phone."""

    if flask.request.form['code'] == login.current_user.phone_verification_code:
        login.current_user.phone_verification_code = None
        login.current_user.phone_verified = True
        DB.session.commit()

        response = {
            'success': True,
        }
    else:
        response = {
            'success': False,
            'message': 'Code mismatch.'
        }

    return flask.Response(json.dumps(response), mimetype='text/json')


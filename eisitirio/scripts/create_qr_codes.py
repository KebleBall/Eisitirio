# coding: utf-8
from __future__ import unicode_literals

import pyqrcode
import base64
import io
import logging
import flask_script as script
# from flask.ext import script
from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.logic.custom_logic import ticket_logic
from eisitirio.helpers import util

APP = app.APP
DB = db.DB
LOG = logging.getLogger(__name__)


class CreateQRCodes(script.Command):
    """Generates ticket QR codes for tickets, and sends them out to ball goers"""
    help = 'Create and send QR codes for ball entrence'

    @staticmethod
    def run():
        with app.APP.app_context():
            send_claim_codes(send_only_new=True)

def generate_barcodes():
    """Given a ticket, generate a 20 character long unique ID for each ticket.
    This will then be used in the QR code that we generate."""
    # Get all the tickets that need to have barcodes added to them
    tickets = models.Ticket.query.filter(
        models.Ticket.barcode == None
    ).all()

    for ticket in tickets:
        # Generate a unique key for this ticket.
        key = util.generate_key(20).decode('utf-8')
        # and add it
        ticket.barcode = key
        DB.session.commit()
    # Return the number of tickets that we generated barcodes for.
    return tickets

def generate_ticket_qr(ticket):
    """
    Generate the QR code for the ticket that we will then feed into the
    email function, that will then email it to the user. We don't store the
    QR codes since that's just a waste of space. Instead, the 'barcode' field
    for the ticket serves as the UUID for the ticket, and we match this up with
    the ticket 'object_id'. This way, people can't go and make their own ticket
    QR codes.
    """
    qrcode_img = pyqrcode.create('{0},{1}'.format(ticket.object_id,
                                                  ticket.barcode))
    buffer = io.BytesIO()
    qrcode_img.png(buffer, scale=20)
    return buffer.getvalue()

def send_claim_code(user):
    """Send qr code to user that holds ticket"""
    if not user.held_ticket:
        LOG.info("Not generating for user {0} since they don't hold a ticket".format(user))
        return False
    elif user.held_ticket.barcode is None:
        LOG.warning("User {0} has a held ticket, but unable to send it to them since there is no barcode for ticket {1}".format(user, user.held_ticket.object_id))
        return False
    else:
        qr_code = generate_ticket_qr(user.held_ticket)
        if qr_code is None:
            LOG.warning("User {0} has a held ticket, but QR generation failed for {1}".format(
                user, user.held_ticket.object_id ))
            return False
        else:
            APP.email_manager.send_image_html(
                user.email,
                'Your Ball Entrance Ticket',
                'ball_ticket.email',
                qr_code,
                user=user
            )
            LOG.info("Sent ticket to {0} holding ticket {1}----{2}".format(user, user.held_ticket.object_id, user.held_ticket.barcode))
        return True

def send_claim_codes(send_only_new=True):
    """Generate barcodes, and send claim codes to all users.
    NOTE: We keep track of the tickets that we have sent out already via
        barcode generation. Thus, if we generate barcodes and don't send then
        we won't send those we generated barcodes for.
    NOTE: if send_only_new is False, then we will send an email with a claim
        code to _all_ users that hold a ticket, whether or not they have previously
        been sent one. Be careful!!
    """
    tickets = generate_barcodes()
    successes = 0
    failures = 0


    if not send_only_new:
        tickets = models.Ticket.query.filter(
            models.Ticket.holder_id != None
        ).all()

    for ticket in tickets:
        if send_claim_code(ticket.holder):
            successes = successes + 1
        else:
            failures = failures + 1

    print "All done sending claim codes. Total #codes that we should have sent: {0}".format(len(tickets))
    print "Total that were sent successfully: {0}".format(successes)
    print "Total that we failed to send successfully: {0}".format(failures)

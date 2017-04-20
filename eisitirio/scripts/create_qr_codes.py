# coding: utf-8
from __future__ import unicode_literals

import pyqrcode
import base64
import io
import logging
from flask.ext import script
from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.logic.custom_logic import ticket_logic
from eisitirio.helpers import util

APP = app.APP
DB = db.DB
LOG = logging.getLogger(__name__)

class CreateQRCodes(script.Command):
    help = 'Create and send QR codes for ball entrence'

    @staticmethod
    def run():
        with app.APP.app_context():
            send_claim_codes(send_only_new=False)


# The flow goes:
# 1. generate_barcodes()
# 2.

def generate_barcodes():
    """Given a ticket, generate a 20 character long unique ID for each ticket.
    This will then be used in the QR code that we """
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

def create_qr_for(user):
    """Given a user, this generates a qrcode for the ticket that they hold for
    entrance into the ball.

    The QR code is generated on the barcode for the ticket. So we have a
    precondition that 'generate_barcodes' has been run before any calls to
    this function are made.
    """

    qrcode_img = None

    if user.held_ticket is not None and user.held_ticket.barcode is None:
        qrcode_img = generate_ticket_qr(user.held_ticket)
        if qrcode_img is None:
            LOG.warning(
            "Failed to generate QR code for ticket {0} for user id {1}".format(
                user.held_ticket.object_id,
                user.object_id
                )
            )
            return None
        else:
            return user.held_ticket.barcode
    elif user.held_ticket is None:
        # If the user doesn't hold a ticket, then we don't need to do anything
        return None
    else:
        return user.held_ticket.barcode

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
        APP.email_manager.send_image_html(
            user.email,
            'Your Ball Entrance Ticket',
            'ball_ticket.email',
            generate_ticket_qr(user.held_ticket),
            user=user
        )
        LOG.info("Sent ticket to {0} holding ticket {1}----{2}".format(user, user.held_ticket.object_id, user.held_ticket.barcode))
        return True

def send_claim_codes(send_only_new=True):
    """Generate barcodes, and send claim codes to all users.
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

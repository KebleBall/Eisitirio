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
from time import sleep

APP = app.APP
DB = db.DB
LOG = logging.getLogger(__name__)


class CreateQRCodes(script.Command):
    """Generates ticket QR codes for tickets, and sends them out to ball goers"""
    help = 'Create and send QR codes for ball entrence'

    @staticmethod
    def run():
        with app.APP.app_context():
            send_claim_codes(send_only_new=False)

def generate_barcodes(send_only_new):
    """Given a ticket, generate a 20 character long unique ID for each ticket.
    This will then be used in the QR code that we generate.

    This returns the tickets that will then be used by 'send_claim_codes'.

    """
    # Get all the tickets that need to have barcodes added to them
    tickets = []
    if send_only_new:
        tickets = models.Ticket.query.filter(
            # We have not sent them an email yet (it has not been "claimed")
            models.Ticket.barcode == None,
            # Ticket has a holder
            models.Ticket.holder_id != None,
            # The ticket is paid for.
            models.Ticket.paid,
            # The ticket has not been cancelled.
            models.Ticket.cancelled == False
        ).all()
    else:
        tickets = models.Ticket.query.filter(
            # Ticket has a holder
            models.Ticket.holder_id != None,
            # The ticket is paid for.
            models.Ticket.paid,
            # The ticket has not been cancelled.
            models.Ticket.cancelled == False
        ).all()

    for ticket in tickets:
        if not ticket.barcode: # Need to generate a bar code
            # Generate a unique key for this ticket.
            key = util.generate_key(20).decode('utf-8')
            # and add it
            ticket.barcode = key
            DB.session.commit()
    # Return the tickets
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
        LOG.info("Not generating for user {0} since they don't hold a ticket".format(user.full_name.encode('utf-8')))
        return False
    elif user.held_ticket.barcode is None:
        LOG.error("User {0} has a held ticket, but unable to send it to them since there is no barcode for ticket {1}".format(user.full_name.encode('utf-8'), user.held_ticket.object_id))
        return False
    else:
        qr_code = generate_ticket_qr(user.held_ticket)
        if qr_code is None:
            LOG.error("User {0} has a held ticket, but QR generation failed for {1}".format(
                user.full_name.encode('utf-8'), user.held_ticket.object_id ))
            return False
        else:
            APP.email_manager.send_image_html(
                user.email,
                'Your Ball Entrance Ticket',
                'ball_ticket.email',
                qr_code,
                user=user
            )
            LOG.info("Sent ticket to {0} holding ticket {1}----{2}".format(user.full_name.encode('utf-8'), user.held_ticket.object_id, user.held_ticket.barcode))
        return True

def send_chunk(tickets):
    successes = 0
    failures = 0

    for ticket in tickets:
        try:
            if send_claim_code(ticket.holder):
                successes = successes + 1
                print '[Sent: {0}]'.format(ticket.object_id)
                LOG.info('[{0}] sent QR code to: {1}'.format(ticket.object_id, ticket.holder.full_name.encode('utf-8')))
            else:
                ticket.barcode = None
                DB.session.commit()
                LOG.error("Failed to send ticket to {0}".format(ticket.holder.full_name.encode('utf-8')))
                print '[Failed to Send: {0}]'.format(ticket.object_id)
                failures = failures + 1
        except:
            # We've failed to send this one out, so mark it for review
            ticket.barcode = None
            DB.session.commit()
            failures = failures + 1
            LOG.error("[EXCEPTION] Possibly failed to send ticket to: {0}".format(ticket.holder.full_name.encode('utf-8')))
        sleep(0.5)

    print "All done sending claim codes. Total #codes that we should have sent: {0}".format(len(tickets))
    print "Total that were sent successfully: {0}".format(successes)
    print "Total that we failed to send successfully: {0}".format(failures)

def send_claim_codes(send_only_new=True):
    """Generate barcodes, and send claim codes to all users.
    NOTE: We keep track of the tickets that we have sent out already via
        barcode generation. Thus, if we generate barcodes and don't send then
        we won't send those we generated barcodes for.
    NOTE: if send_only_new is False, then we will send an email with a claim
        code to _all_ users that hold a ticket, whether or not they have previously
        been sent one. Be careful!!
    """
    tickets = generate_barcodes(send_only_new)

    send_chunk(tickets)

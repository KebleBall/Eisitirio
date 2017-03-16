# coding: utf-8
"""Script to update battels accounts for keblites that were overcharged"""

from __future__ import unicode_literals

import qrcode
import base64
from flask.ext import script
from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.logic.custom_logic import ticket_logic

APP = app.APP
DB = db.DB
QRFACTORY = qrcode.image.svg.SvgImage

def create_qr_for(user):
    """Given a user, this generates a qrcode for the ticket that they hold for
    entrance into the ball."""

    qrcode_img = None

    if ticket.can_be_collected():
        qrcode_img = qrcode.make(user.held_ticket.object_id, image_factory=QRFACTORY)

    return qrcode_img

def add_qr_to(user):
    """Given a user, this generates the qrcode for their held ticket and then
    adds that to the ticket"""

    qrcode_img = create_qr_for(user)

    if qrcode_img is None:
        return None

    user.held_ticket.barcode = base64.b64encode(qrcode_img)

    DB.session.commit()

    return user.held_ticket.barcode


def send_claim_code(user):
    """Send qr code to user that holds ticket"""
    APP.email_manager.send_template(
        user.email,
        'IMPORTANT: Ball entrance ticket',
        'ball_ticket.email',
        user=user
    )

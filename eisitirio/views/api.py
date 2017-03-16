# coding: utf-8
"""Views related to the purchase process."""

from __future__ import unicode_literals

from flask.ext import login
import flask
from sqlalchemy import or_

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

APP = app.APP
DB = db.DB

API = flask.Blueprint('api', __name__)

@API.route('/api/verify-ticket/<int:ticket_id>')
def api_verify_ticket(ticket_id):
    ticket = models.Ticket.get_by_id(ticket_id)

    print ticket

    if ticket is not None:
        return "true"
    else:
        return "false"

# coding: utf-8
"""Views related to the group purchase process."""

from __future__ import unicode_literals

from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.logic import purchase_logic
from eisitirio.logic import payment_logic

APP = app.APP
DB = db.DB

GROUP_PURCHASE = flask.Blueprint('group_purchase', __name__)

@GROUP_PURCHASE.route('/purchase/group/dashboard', methods=['GET', 'POST'])
@login.login_required
def group_purchase_dashboard():
    """Display the group purchase dashboard."""
    ticket_info = purchase_logic.get_group_ticket_info(login.current_user)

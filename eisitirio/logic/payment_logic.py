# coding: utf-8
"""Business logic functions for payment and money handling."""

from __future__ import unicode_literals

from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

def do_payment(tickets, postage_option, payment_method, payment_term,
               address=None):
    """Run the payment process for tickets and postage.

    Args:
        tickets: (models.Ticket) The tickets the user is paying for.
        postage_option: (eisitirio.helpers.postage_option.PostageOption) The
            postage option selected by the user.
        payment_method: (str) The payment method selected by the user.
        payment_term: (str or None) If the user selected to pay by Battels, the
            coded term to charge the transaction to.
        address: (str or None) The address to post the tickets to.

    Returns:
        A flask redirect, either to the dashboard, or to the payment gateway.
    """
    if any(ticket.price > 0 for ticket in tickets) or postage_option.price > 0:
        if payment_method == 'Battels':
            transaction = models.BattelsTransaction(login.current_user)
        elif payment_method == 'Card':
            transaction = models.CardTransaction(login.current_user)
    else:
        transaction = models.FreeTransaction(login.current_user)

        app.APP.log_manager.log_event(
            'Performed Free Transaction',
            tickets=tickets,
            user=login.current_user,
            transaction=transaction,
            commit=False
        )

    items = [
        models.TicketTransactionItem(transaction, ticket)
        for ticket in tickets
    ]

    if postage_option is not app.APP.config['NO_POSTAGE_OPTION']:
        postage = models.Postage(postage_option, tickets, address)

        items.append(
            models.PostageTransactionItem(transaction, postage)
        )

        db.DB.session.add(postage)

    db.DB.session.add(transaction)
    db.DB.session.add_all(items)
    db.DB.session.commit()

    if payment_method == 'Battels':
        transaction.charge(payment_term)

        db.DB.session.commit()
    elif payment_method == 'Card':
        eway_url = transaction.get_eway_url()

        if eway_url:
            return flask.redirect(eway_url)

    return flask.redirect(flask.url_for('dashboard.dashboard_home'))

# coding: utf-8
"""Business logic functions for payment and money handling."""

from __future__ import unicode_literals

from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.logic import eway_logic

def get_transaction(tickets, postage_option, payment_method):
    """Get a new transaction object for the given items."""
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

    return transaction

def create_postage(transaction, tickets, postage_option, address):
    """Create a postage object and corresponding transaction item."""
    if postage_option is not app.APP.config['NO_POSTAGE_OPTION']:
        postage = models.Postage(postage_option, tickets, address)

        db.DB.session.add(postage)

        db.DB.session.add(models.PostageTransactionItem(transaction, postage))

def complete_payment(transaction, payment_method, payment_term):
    """Do the payment, or redirect the user to eWay."""
    if payment_method == 'Battels':
        transaction.charge(payment_term)

        db.DB.session.commit()
    elif payment_method == 'Card':
        payment_url = eway_logic.get_payment_url(transaction)

        if payment_url:
            return flask.redirect(payment_url)

    return flask.redirect(flask.url_for('dashboard.dashboard_home'))

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
    transaction = get_transaction(tickets, postage_option, payment_method)

    db.DB.session.add(transaction)

    db.DB.session.add_all(
        models.TicketTransactionItem(transaction, ticket)
        for ticket in tickets
    )

    create_postage(transaction, tickets, postage_option, address)

    db.DB.session.commit()

    return complete_payment(transaction, payment_method, payment_term)

def buy_postage(tickets, postage_option, payment_method, payment_term,
                address=None):
    """Run the payment process for postage only.

    Args:
        tickets: (models.Ticket) The tickets the user is buying postage for.
        postage_option: (eisitirio.helpers.postage_option.PostageOption) The
            postage option selected by the user.
        payment_method: (str) The payment method selected by the user.
        payment_term: (str or None) If the user selected to pay by Battels, the
            coded term to charge the transaction to.
        address: (str or None) The address to post the tickets to.

    Returns:
        A flask redirect, either to the dashboard, or to the payment gateway.
    """
    transaction = get_transaction([], postage_option, payment_method)

    db.DB.session.add(transaction)

    create_postage(transaction, tickets, postage_option, address)

    db.DB.session.commit()

    return complete_payment(transaction, payment_method, payment_term)

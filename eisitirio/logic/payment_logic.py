# coding: utf-8
"""Business logic functions for payment and money handling."""

from __future__ import unicode_literals

from flask.ext import login
import flask

from eisitirio.database import db
from eisitirio.database import models

def do_payment(tickets, postage, payment_method, payment_term, address=None):
    """Run the payment process for tickets and postage.

    Args:
        tickets: (models.Ticket) The tickets the user is paying for.
        postage: (eisitirio.helpers.postage_option.PostageOption) The postage
            option selected by the user.
        payment_method: (str) The payment method selected by the user.
        payment_term: (str or None) If the user selected to pay by Battels, the
            coded term to charge the transaction to.
        address: (str or None) The address to post the tickets to.

    Returns:
        A flask redirect, either to the dashboard, or to the payment gateway.
    """
    transaction = models.Transaction(login.current_user, address)

    db.DB.session.add(transaction)
    db.DB.session.commit()

    items = [models.TransactionItem(transaction, ticket) for ticket in tickets]

    if postage:
        items.append(
            models.TransactionItem(transaction, None, 'Postage', postage.price,
                                   postage.name)
        )

    db.DB.session.add_all(items)
    db.DB.session.commit()

    if payment_method == 'Battels':
        transaction.charge_to_battels(payment_term)

        db.DB.session.commit()

        return flask.redirect(flask.url_for('dashboard.dashboard_home'))
    else:
        card_transaction = transaction.charge_to_card()

        eway_url = card_transaction.get_eway_url()

        if eway_url:
            db.DB.session.add(card_transaction)
            db.DB.session.commit()

            return flask.redirect(eway_url)
        else:
            return flask.redirect(flask.url_for('dashboard.dashboard_home'))

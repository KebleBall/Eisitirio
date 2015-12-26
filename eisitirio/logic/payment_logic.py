# coding: utf-8
"""Business logic functions for payment and money handling."""

from __future__ import unicode_literals

from flask.ext import login
import flask

from eisitirio.database import db
from eisitirio.database import models

def do_payment(tickets, postage, payment_method, payment_term, address=None):
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

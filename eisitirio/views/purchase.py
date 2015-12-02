# coding: utf-8
"""Views related to the purchase process."""

from __future__ import unicode_literals

from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import validators
from eisitirio.logic import purchase_logic
from eisitirio.logic import payment_logic

APP = app.APP
DB = db.DB

PURCHASE = flask.Blueprint('purchase', __name__)

@PURCHASE.route('/purchase', methods=['GET', 'POST'])
@login.login_required
def purchase_home():
    """First step of the purchasing flow.

    Checks if the user can purchase tickets, and processes the purchase form.
    """
    ticket_info = purchase_logic.get_ticket_info(
        login.current_user
    )

    if not ticket_info.ticket_types:
        flask.flash(
            'You are not able to purchase tickets at this time.',
            'info'
        )

        (waiting_permitted, _, _) = login.current_user.can_wait()
        if waiting_permitted:
            flask.flash(
                (
                    'Please join the waiting list, and you will be allocated '
                    'tickets as they become available'
                ),
                'info'
            )
            return flask.redirect(flask.url_for('purchase.wait'))
        else:
            return flask.redirect(flask.url_for('dashboard.dashboard_home'))

    num_tickets = {
        ticket_type.slug: 0
        for ticket_type, _ in ticket_info.ticket_types
    }

    ticket_names = []

    if flask.request.method == 'POST':
        for ticket_type, _ in ticket_info.ticket_types:
            num_tickets[ticket_type.slug] = int(
                flask.request.form['num_tickets_{0}'.format(ticket_type.slug)]
            )

        ticket_names = [
            name
            for name in flask.request.form.getlist('ticket_name[]')
            if name
        ]

        flashes = purchase_logic.validate_tickets(
            ticket_info,
            num_tickets,
            ticket_names
        )

        payment_method, payment_term = purchase_logic.check_payment_method(
            flashes
        )

        voucher = None
        if (
                'voucher_code' in flask.request.form and
                flask.request.form['voucher_code'] != ''
        ):
            (result, response, voucher) = validators.validate_voucher(
                flask.request.form['voucher_code'])
            if not result:
                flashes.append(
                    (
                        '{} Please clear the discount code field to continue '
                        'without using a voucher.'
                    ).format(response['message'])
                )

        postage, address = purchase_logic.check_postage(flashes)

        if flashes:
            flask.flash(
                (
                    'There were errors in your order. Please fix '
                    'these and try again'
                ),
                'error'
            )
            for msg in flashes:
                flask.flash(msg, 'warning')

            return flask.render_template(
                'purchase/purchase_home.html',
                form=flask.request.form,
                ticket_names=ticket_names,
                num_tickets=num_tickets,
                ticket_info=ticket_info
            )

        tickets = purchase_logic.create_tickets(
            login.current_user,
            ticket_info,
            num_tickets,
            ticket_names
        )

        if voucher is not None:
            (success, tickets, error) = voucher.apply(tickets,
                                                      login.current_user)
            if not success:
                flask.flash('Could not use voucher - ' + error, 'error')

        DB.session.add_all(tickets)
        DB.session.commit()

        APP.log_manager.log_event(
            'Purchased Tickets',
            tickets,
            login.current_user
        )

        return payment_logic.do_payment(
            tickets,
            postage,
            payment_method,
            payment_term,
            address
        )
    else:
        return flask.render_template(
            'purchase/purchase_home.html',
            num_tickets=num_tickets,
            ticket_names=ticket_names,
            ticket_info=ticket_info
        )

@PURCHASE.route('/purchase/wait', methods=['GET', 'POST'])
@login.login_required
def wait():
    """Handles joining the waiting list.

    Checks if the user can join the waiting list, and processes the form to
    create the requisite waiting list entry.
    """
    (
        wait_permitted,
        wait_available,
        can_wait_message
    ) = login.current_user.can_wait()

    if not wait_permitted:
        flask.flash(
            (
                'You cannot join the waiting list at this time because ' +
                can_wait_message
            ),
            'info'
        )
        return flask.redirect(flask.url_for('dashboard.dashboard_home'))

    if flask.request.method == 'POST':
        valid = True
        flashes = []

        num_tickets = int(flask.request.form['num_tickets'])

        if num_tickets > wait_available:
            valid = False
            flashes.append('You cannot wait for that many tickets')
        elif num_tickets < 1:
            valid = False
            flashes.append('You must wait for at least 1 ticket')

        if not valid:
            flask.flash(
                (
                    'There were errors in your order. Please fix '
                    'these and try again'
                ),
                'error'
            )
            for msg in flashes:
                flask.flash(msg, 'warning')

            return flask.render_template(
                'purchase/wait.html',
                form=flask.request.form,
                num_tickets=num_tickets,
                wait_available=wait_available
            )

        DB.session.add(
            models.Waiting(
                login.current_user,
                num_tickets
            )
        )
        DB.session.commit()

        APP.log_manager.log_event(
            'Joined waiting list for {0} tickets'.format(
                num_tickets
            ),
            [],
            login.current_user
        )

        flask.flash(
            (
                'You have been added to the waiting list for {0} ticket{1}.'
            ).format(
                num_tickets,
                '' if num_tickets == 1 else 's'
            ),
            'success'
        )

        return flask.redirect(flask.url_for('dashboard.dashboard_home'))
    else:
        return flask.render_template(
            'purchase/wait.html',
            wait_available=wait_available
        )

@PURCHASE.route('/purchase/eway-success/<int:object_id>')
def eway_success(object_id):
    """Callback from a successful eWay transaction.

    The user is redirected back to this page from the payment gateway once the
    transaction has been completed successfully (not necessarily implying that
    the payment was completed successfully).

    Has the transaction object process the result of the transaction, and
    redirects to the dashboard.
    """
    transaction = models.CardTransaction.get_by_id(object_id)

    transaction.process_eway_payment()

    return flask.redirect(flask.url_for('dashboard.dashboard_home'))

@PURCHASE.route('/purchase/eway-cancel/<int:object_id>')
def eway_cancel(object_id):
    """Callback from a cancelled eWay transaction.

    The user is redirected back to this page from the payment gateway if they
    cancel the transaction.

    Marks the transaction as cancelled and redirects to the dashboard.
    """
    transaction = models.CardTransaction.get_by_id(object_id)

    transaction.cancel_eway_payment()

    return flask.redirect(flask.url_for('dashboard.dashboard_home'))

@PURCHASE.route('/purchase/complete-payment', methods=['GET', 'POST'])
def complete_payment():
    if flask.request.method == 'POST':
        flashes = []

        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(flask.request.form.getlist('tickets[]'))
        ).filter(
            models.Ticket.owner_id == login.current_user.object_id
        ).filter(
            models.Ticket.paid == False
        ).all()

        if not tickets:
            flashes.append('You have not selected any tickets to pay for.')

        method, term = purchase_logic.check_payment_method(flashes)

        postage, address = purchase_logic.check_postage(flashes)

        if flashes:
            flask.flash(
                (
                    'There were errors in your order. Please fix '
                    'these and try again'
                ),
                'error'
            )
            for msg in flashes:
                flask.flash(msg, 'warning')

            return flask.render_template(
                'purchase/complete_payment.html',
                form=flask.request.form
            )

        return payment_logic.do_payment(
            tickets,
            postage,
            method,
            term,
            address
        )
    else:
        return flask.render_template(
            'purchase/complete_payment.html'
        )

# coding: utf-8
"""Views related to the purchase process."""

from __future__ import unicode_literals

from flask.ext import login
import flask

from kebleball import app
from kebleball.database import db
from kebleball.database import models
from kebleball.helpers import validators

APP = app.APP
DB = db.DB

PURCHASE = flask.Blueprint('purchase', __name__)

@PURCHASE.route('/purchase', methods=['GET', 'POST'])
@login.login_required
def purchase_home():
    """First step of the purchasing flow.

    Checks if the user can purchase tickets, and processes the purchase form.
    """
    (
        buying_permitted,
        tickets_available,
        can_buy_message
    ) = login.current_user.can_buy()

    if not buying_permitted:
        flask.flash(
            'You cannot currently purchase tickets, because '
            + can_buy_message, 'info'
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

    if flask.request.method == 'POST':
        valid = True
        flashes = []

        num_tickets = int(flask.request.form['num_tickets'])

        if num_tickets > tickets_available:
            valid = False
            flashes.append('You cannot buy that many tickets')
        elif num_tickets < 1:
            valid = False
            flashes.append('You must purchase at least 1 ticket')

        if 'payment_method' not in flask.request.form:
            valid = False
            flashes.append('You must select a payment method')
        elif flask.request.form['payment_method'] not in [
                'Cash',
                'Card',
                'Cheque',
                'Battels'
        ]:
            valid = False
            flashes.append('That is not a valid payment method')
        elif (flask.request.form['payment_method'] == 'Battels'
              and not login.current_user.can_pay_by_battels()):
            valid = False
            flashes.append('You cannot pay by battels')
        elif (
                flask.request.form['payment_method'] == 'Cash' or
                flask.request.form['payment_method'] == 'Cheque'
        ) and (
            'payment_reason' not in flask.request.form or
            flask.request.form['payment_reason'] == ''
        ):
            valid = False
            flashes.append('You must give a reason for paying by cash/cheque.')

        if 'accept_terms' not in flask.request.form:
            valid = False
            flashes.append('You must accept the Terms and Conditions')

        voucher = None
        if (
                'voucher_code' in flask.request.form and
                flask.request.form['voucher_code'] != ''
        ):
            (result, response, voucher) = validators.validate_voucher(
                flask.request.form['voucher_code'])
            if not result:
                valid = False
                flashes.append(
                    (
                        '{} Please clear the discount code field to continue '
                        'without using a voucher.'
                    ).format(response['message'])
                )

        referrer = None
        if ('referrer_email' in flask.request.form
                and flask.request.form['referrer_email'] != ''):
            (result, response, referrer) = validators.validate_referrer(
                flask.request.form['referrer_email'], login.current_user)
            if not result:
                valid = False
                flashes.append(
                    (
                        '{} Please clear the referrer field to continue '
                        'without giving somebody credit.'
                    ).format(response['message'])
                )

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
                'purchase/purchase_home.html',
                form=flask.request.form,
                num_tickets=num_tickets,
                can_buy=tickets_available
            )

        tickets = []

        if login.current_user.gets_discount():
            tickets.append(
                models.Ticket(
                    login.current_user,
                    flask.request.form['payment_method'],
                    (
                        login.current_user.get_base_ticket_price() -
                        APP.config['KEBLE_DISCOUNT']
                    )
                )
            )
            start = 1
        else:
            start = 0

        for _ in xrange(start, num_tickets):
            tickets.append(
                models.Ticket(
                    login.current_user,
                    flask.request.form['payment_method'],
                    login.current_user.get_base_ticket_price()
                )
            )

        if (
                flask.request.form['payment_method'] == 'Cash' or
                flask.request.form['payment_method'] == 'Cheque'
        ):
            for ticket in tickets:
                ticket.add_note(
                    flask.request.form['payment_method'] +
                    ' payment reason: ' +
                    flask.request.form['payment_reason']
                )

        if voucher is not None:
            (success, tickets, error) = voucher.apply(tickets,
                                                      login.current_user)
            if not success:
                flask.flash('Could not use Voucher - ' + error, 'error')

        if referrer is not None:
            for ticket in tickets:
                ticket.set_referrer(referrer)

        DB.session.add_all(tickets)
        DB.session.commit()

        APP.log_manager.log_event(
            'Purchased Tickets',
            tickets,
            login.current_user
        )

        expires = None
        for ticket in tickets:
            if (
                    expires == None or
                    ticket.expires < expires
            ):
                expires = ticket.expires

        total_value = sum([ticket.price for ticket in tickets])

        flask.flash(
            (
                '{0} tickets have been reserved for you at a total cost of '
                '&pound;{1:.2f}.'
            ).format(
                num_tickets,
                total_value / 100.0
            ),
            'success'
        )

        if total_value > 0:
            flask.flash(
                (
                    'You must set a name on your tickets before they can be '
                    'paid for. Please set names on your tickets and then '
                    'click the "Complete Payment" button. You must complete '
                    'payment for these tickets by {0}'
                ).format(
                    expires.strftime('%H:%M %d/%m/%Y')
                ),
                'info'
            )
        else:
            flask.flash('Please set names for these tickets before collection',
                        'info')
        return flask.redirect(flask.url_for('dashboard.dashboard_home'))
    else:
        return flask.render_template(
            'purchase/purchase_home.html',
            can_buy=tickets_available
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

        if 'accept_terms' not in flask.request.form:
            valid = False
            flashes.append('You must accept the Terms and Conditions')

        referrer = None
        if ('referrer_email' in flask.request.form
                and flask.request.form['referrer_email'] != ''):
            (result, response, referrer) = validators.validate_referrer(
                flask.request.form['referrer_email'], login.current_user)
            if not result:
                valid = False
                flashes.append(
                    (
                        '{} Please clear the referrer field to continue '
                        'without giving somebody credit.'
                    ).format(response['message'])
                )

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
                'purchase/purchase_home.html',
                form=flask.request.form,
                num_tickets=num_tickets,
                can_wait=wait_available
            )

        DB.session.add(
            models.Waiting(
                login.current_user,
                num_tickets,
                referrer
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
            can_wait=wait_available
        )

@PURCHASE.route('/purchase/change-method', methods=['GET', 'POST'])
@login.login_required
def change_method():
    """Change the payment method for one or more tickets.

    Displays a list of unpaid tickets with checkboxes, and processes the form.
    """
    if flask.request.method == 'POST':
        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(flask.request.form.getlist('tickets[]'))
        ).filter(
            models.Ticket.owner_id == login.current_user.object_id
        ).filter(
            models.Ticket.paid == False
        ).all()

        while None in tickets:
            tickets.remove(None)

        if (
                (
                    flask.request.form['payment_method'] == 'Cash' or
                    flask.request.form['payment_method'] == 'Cheque'
                ) and (
                    'payment_reason' not in flask.request.form or
                    flask.request.form['payment_reason'] == ''
                )
        ):
            flask.flash('You must give a reason for paying by cash or cheque.',
                        'error')
            return flask.render_template(
                'purchase/change_method.html',
                tickets=flask.request.form.getlist('tickets[]')
            )
        elif 'payment_reason' in flask.request.form:
            reason = flask.request.form['payment_reason']
        else:
            reason = None

        for ticket in tickets:
            ticket.set_payment_method(flask.request.form['payment_method'],
                                      reason)

        DB.session.commit()

        APP.log_manager.log_event(
            'Changed Payment Method to {0}'.format(
                flask.request.form['payment_method']
            ),
            tickets,
            login.current_user
        )

        flask.flash(
            (
                'The payment method on the selected tickets has been changed '
                'successfully'
            ),
            'success'
        )

    return flask.render_template('purchase/change_method.html')

@PURCHASE.route('/purchase/card-confirm', methods=['GET', 'POST'])
@login.login_required
def card_confirm():
    """Complete a card payment.

    Presents a list of tickets due for card payment, and processes the form to
    create a CardTransaction object and flask.redirect the user to the payment
    gateway.
    """
    if flask.request.method == 'POST':
        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(flask.request.form.getlist('tickets[]'))
        ).filter(
            models.Ticket.owner_id == login.current_user.object_id
        ).filter(
            models.Ticket.paid == False
        ).all()

        while None in tickets:
            tickets.remove(None)

        transaction = models.CardTransaction(
            login.current_user,
            tickets
        )

        DB.session.add(transaction)
        DB.session.commit()

        eway_url = transaction.get_eway_url()

        if eway_url is not None:
            return flask.redirect(eway_url)

    return flask.render_template('purchase/card_confirm.html')

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

@PURCHASE.route('/purchase/battels-confirm', methods=['GET', 'POST'])
@login.login_required
def battels_confirm():
    """Complete a card payment.

    Presents a list of tickets due for battels payment and presents an option of
    which term to charge the tickets to. Upon submission processes the form to
    add the charge to users battels account.
    """
    if not login.current_user.can_pay_by_battels():
        flask.flash(
            'You cannot currently pay by battels. Please change the payment '
            'method on your tickets',
            'warning'
        )
        return flask.redirect(flask.url_for('purchase.change_method'))

    if flask.request.method == 'POST':
        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(flask.request.form.getlist('tickets[]'))
        ).filter(
            models.Ticket.owner_id == login.current_user.object_id
        ).filter(
            models.Ticket.paid == False
        ).all()

        while None in tickets:
            tickets.remove(None)

        if (
                APP.config['CURRENT_TERM'] == 'HT' and
                flask.request.form['payment_term'] != 'HT'
        ):
            flask.flash('Invalid choice of payment term', 'warning')
        else:
            battels = login.current_user.battels

            for ticket in tickets:
                battels.charge(ticket, flask.request.form['payment_term'])

            DB.session.commit()

            APP.log_manager.log_event(
                'Confirmed battels payment',
                tickets,
                login.current_user
            )

            flask.flash('Your battels payment has been confirmed', 'success')

    return flask.render_template('purchase/battels_confirm.html')

@PURCHASE.route('/purchase/cancel', methods=['GET', 'POST'])
@login.login_required
def cancel():
    """Cancel tickets.

    Presents the user with a list of tickets, and upon form submission cancels
    the selected tickets, giving refunds as appropriate.
    """
    if flask.request.method == 'POST':
        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(flask.request.form.getlist('tickets[]'))
        ).filter(
            models.Ticket.owner_id == login.current_user.object_id
        ).all()

        while None in tickets:
            tickets.remove(None)

        tickets = [x for x in tickets if x.can_be_cancelled_automatically()]

        card_transactions = {}

        cancelled = []

        for ticket in tickets:
            if not ticket.paid:
                ticket.cancelled = True
                DB.session.commit()
                cancelled.append(ticket)
            elif ticket.payment_method == 'Free':
                ticket.cancelled = True
                DB.session.commit()
                cancelled.append(ticket)
            elif ticket.payment_method == 'Battels':
                ticket.battels.cancel(ticket)
                cancelled.append(ticket)
            elif ticket.payment_method == 'Card':
                if ticket.card_transaction_id in card_transactions:
                    transaction = card_transactions[ticket.card_transaction_id]
                    transaction['tickets'].append(ticket)
                else:
                    card_transactions[ticket.card_transaction_id] = {
                        'transaction': ticket.card_transaction,
                        'tickets': [ticket]
                    }

        refund_failed = False

        for transaction in card_transactions.itervalues():
            value = sum([t.price for t in transaction['tickets']])

            if transaction['transaction'].process_refund(value):
                cancelled.extend(transaction['tickets'])
                for ticket in transaction['tickets']:
                    ticket.cancelled = True
                DB.session.commit()
            else:
                refund_failed = True

        if refund_failed:
            flask.flash(
                (
                    'Some of your tickets could not be automatically '
                    'refunded, and so were not cancelled. You can try again '
                    'later, but if this problem continues to occur, you '
                    'should contact <a href="{0}">the ticketing officer</a>'
                ).format(
                    APP.config['TICKETS_EMAIL_LINK']
                ),
                'warning'
            )

        if len(cancelled) > 0:
            APP.log_manager.log_event(
                'Cancelled tickets',
                cancelled,
                login.current_user
            )

            if refund_failed:
                flask.flash(
                    (
                        'Some of the tickets you selected have been '
                        'cancelled. See other messages for details.'
                    ),
                    'info'
                )
            else:
                flask.flash(
                    'All of the tickets you selected have been cancelled.',
                    'info'
                )

    return flask.render_template('purchase/cancel.html')

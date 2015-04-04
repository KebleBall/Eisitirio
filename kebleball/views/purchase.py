# coding: utf-8
"""Views related to the purchase process."""

from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask.ext import login

from kebleball import app
from kebleball.database import db
from kebleball.database import models
from kebleball.helpers import validators

APP = app.APP
DB = db.DB

PURCHASE = Blueprint('purchase', __name__)

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
        flash(
            u'You cannot currently purchase tickets, because '
            + can_buy_message, 'info'
        )

        (waiting_permitted, _, _) = login.current_user.canWait()
        if waiting_permitted:
            flash(
                (
                    u'Please join the waiting list, and you will be allocated '
                    u'tickets as they become available'
                ),
                'info'
            )
            return redirect(url_for('purchase.wait'))
        else:
            return redirect(url_for('dashboard.dashboard_home'))

    if request.method == 'POST':
        valid = True
        flashes = []

        num_tickets = int(request.form['num_tickets'])

        if num_tickets > tickets_available:
            valid = False
            flashes.append(u'You cannot buy that many tickets')
        elif num_tickets < 1:
            valid = False
            flashes.append(u'You must purchase at least 1 ticket')

        if 'paymentMethod' not in request.form:
            valid = False
            flashes.append(u'You must select a payment method')
        elif request.form['paymentMethod'] not in [
                'Cash',
                'Card',
                'Cheque',
                'Battels'
        ]:
            valid = False
            flashes.append(u'That is not a valid payment method')
        elif (request.form['paymentMethod'] == 'Battels'
              and not login.current_user.can_pay_by_battels()):
            valid = False
            flashes.append(u'You cannot pay by battels')
        elif (
                request.form['paymentMethod'] == 'Cash' or
                request.form['paymentMethod'] == 'Cheque'
        ) and (
            'paymentReason' not in request.form or
            request.form['paymentReason'] == ''
        ):
            valid = False
            flashes.append(u'You must give a reason for paying by cash/cheque.')

        if 'acceptTerms' not in request.form:
            valid = False
            flashes.append(u'You must accept the Terms and Conditions')

        voucher = None
        if 'voucherCode' in request.form and request.form['voucherCode'] != '':
            (result, response, voucher) = validators.validateVoucher(
                request.form['voucherCode'])
            if not result:
                valid = False
                flashes.append(
                    (
                        u'{} Please clear the discount code field to continue '
                        u'without using a voucher.'
                    ).format(response['message'])
                )

        referrer = None
        if ('referrerEmail' in request.form
                and request.form['referrerEmail'] != ''):
            (result, response, referrer) = validators.validateReferrer(
                request.form['referrerEmail'], login.current_user)
            if not result:
                valid = False
                flashes.append(
                    (
                        u'{} Please clear the referrer field to continue '
                        u'without giving somebody credit.'
                    ).format(response['message'])
                )

        if not valid:
            flash(
                (
                    u'There were errors in your order. Please fix '
                    u'these and try again'
                ),
                'error'
            )
            for msg in flashes:
                flash(msg, 'warning')

            return render_template(
                'purchase/purchase_home.html',
                form=request.form,
                num_tickets=num_tickets,
                canBuy=tickets_available
            )

        tickets = []

        if login.current_user.gets_discount():
            tickets.append(
                models.Ticket(
                    login.current_user,
                    request.form['paymentMethod'],
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
                    request.form['paymentMethod'],
                    login.current_user.get_base_ticket_price()
                )
            )

        if (
                request.form['paymentMethod'] == 'Cash' or
                request.form['paymentMethod'] == 'Cheque'
        ):
            for ticket in tickets:
                ticket.add_note(
                    request.form['paymentMethod'] +
                    ' payment reason: ' +
                    request.form['paymentReason']
                )

        if voucher is not None:
            (success, tickets, error) = voucher.apply(tickets,
                                                      login.current_user)
            if not success:
                flash('Could not use Voucher - ' + error, 'error')

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

        flash(
            (
                u'{0} tickets have been reserved for you at a total cost of '
                u'&pound;{1:.2f}.'
            ).format(
                num_tickets,
                total_value / 100.0
            ),
            'success'
        )

        if total_value > 0:
            flash(
                (
                    u'You must set a name on your tickets before they can be '
                    u'paid for. Please set names on your tickets and then '
                    u'click the "Complete Payment" button. You must complete '
                    u'payment for these tickets by {0}'
                ).format(
                    expires.strftime('%H:%M %d/%m/%Y')
                ),
                'info'
            )
        else:
            flash(u'Please set names for these tickets before collection',
                  u'info')
        return redirect(url_for('dashboard.dashboardHome'))
    else:
        return render_template(
            'purchase/purchase_home.html',
            canBuy=tickets_available
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
    ) = login.current_user.canWait()

    if not wait_permitted:
        flash(
            (
                u'You cannot join the waiting list at this time because ' +
                can_wait_message
            ),
            'info'
        )
        return redirect(url_for('dashboard.dashboard_home'))

    if request.method == 'POST':
        valid = True
        flashes = []

        num_tickets = int(request.form['num_tickets'])

        if num_tickets > wait_available:
            valid = False
            flashes.append(u'You cannot wait for that many tickets')
        elif num_tickets < 1:
            valid = False
            flashes.append(u'You must wait for at least 1 ticket')

        if 'acceptTerms' not in request.form:
            valid = False
            flashes.append(u'You must accept the Terms and Conditions')

        referrer = None
        if ('referrerEmail' in request.form
                and request.form['referrerEmail'] != ''):
            (result, response, referrer) = validators.validateReferrer(
                request.form['referrerEmail'], login.current_user)
            if not result:
                valid = False
                flashes.append(
                    (
                        u'{} Please clear the referrer field to continue '
                        u'without giving somebody credit.'
                    ).format(response['message'])
                )

        if not valid:
            flash(
                (
                    u'There were errors in your order. Please fix '
                    u'these and try again'
                ),
                'error'
            )
            for msg in flashes:
                flash(msg, 'warning')

            return render_template(
                'purchase/purchase_home.html',
                form=request.form,
                num_tickets=num_tickets,
                canWait=wait_available
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

        flash(
            (
                u'You have been added to the waiting list for {0} ticket{1}.'
            ).format(
                num_tickets,
                '' if num_tickets == 1 else 's'
            ),
            'success'
        )

        return redirect(url_for('dashboard.dashboard_home'))
    else:
        return render_template(
            'purchase/wait.html',
            canWait=wait_available
        )

@PURCHASE.route('/purchase/change-method', methods=['GET', 'POST'])
@login.login_required
def change_method():
    """Change the payment method for one or more tickets.

    Displays a list of unpaid tickets with checkboxes, and processes the form.
    """
    if request.method == 'POST':
        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(request.form.getlist('tickets[]'))
        ).filter(
            models.Ticket.owner_id == login.current_user.object_id
        ).filter(
            models.Ticket.paid == False
        ).all()

        while None in tickets:
            tickets.remove(None)

        if (
                (
                    request.form['paymentMethod'] == 'Cash' or
                    request.form['paymentMethod'] == 'Cheque'
                ) and (
                    'paymentReason' not in request.form or
                    request.form['paymentReason'] == ''
                )
        ):
            flash(u'You must give a reason for paying by cash or cheque.',
                  u'error')
            return render_template(
                'purchase/change_method.html',
                tickets=request.form.getlist('tickets[]')
            )
        elif 'paymentReason' in request.form:
            reason = request.form['paymentReason']
        else:
            reason = None

        for ticket in tickets:
            ticket.set_payment_method(request.form['paymentMethod'], reason)

        DB.session.commit()

        APP.log_manager.log_event(
            'Changed Payment Method to {0}'.format(
                request.form['paymentMethod']
            ),
            tickets,
            login.current_user
        )

        flash(
            (
                u'The payment method on the selected tickets has been changed '
                u'successfully'
            ),
            'success'
        )

    return render_template('purchase/change_method.html')

@PURCHASE.route('/purchase/card-confirm', methods=['GET', 'POST'])
@login.login_required
def card_confirm():
    """Complete a card payment.

    Presents a list of tickets due for card payment, and processes the form to
    create a CardTransaction object and redirect the user to the payment
    gateway.
    """
    if request.method == 'POST':
        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(request.form.getlist('tickets[]'))
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
            return redirect(eway_url)

    return render_template('purchase/card_confirm.html')

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

    return redirect(url_for('dashboard.dashboard_home'))

@PURCHASE.route('/purchase/eway-cancel/<int:object_id>')
def eway_cancel(object_id):
    """Callback from a cancelled eWay transaction.

    The user is redirected back to this page from the payment gateway if they
    cancel the transaction.

    Marks the transaction as cancelled and redirects to the dashboard.
    """
    transaction = models.CardTransaction.get_by_id(object_id)

    transaction.cancel_eway_payment()

    return redirect(url_for('dashboard.dashboard_home'))

@PURCHASE.route('/purchase/battels-confirm', methods=['GET', 'POST'])
@login.login_required
def battels_confirm():
    """Complete a card payment.

    Presents a list of tickets due for battels payment and presents an option of
    which term to charge the tickets to. Upon submission processes the form to
    add the charge to users battels account.
    """
    if not login.current_user.can_pay_by_battels():
        flash(
            u'You cannot currently pay by battels. Please change the payment '
            u'method on your tickets',
            'warning'
        )
        return redirect(url_for('purchase.change_method'))

    if request.method == 'POST':
        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(request.form.getlist('tickets[]'))
        ).filter(
            models.Ticket.owner_id == login.current_user.object_id
        ).filter(
            models.Ticket.paid == False
        ).all()

        while None in tickets:
            tickets.remove(None)

        if (
                APP.config['CURRENT_TERM'] == 'HT' and
                request.form['paymentTerm'] != 'HT'
        ):
            flash(u'Invalid choice of payment term', 'warning')
        else:
            battels = login.current_user.battels

            for ticket in tickets:
                battels.charge(ticket, request.form['paymentTerm'])

            DB.session.commit()

            APP.log_manager.log_event(
                'Confirmed battels payment',
                tickets,
                login.current_user
            )

            flash(u'Your battels payment has been confirmed', 'success')

    return render_template('purchase/battels_confirm.html')

@PURCHASE.route('/purchase/cancel', methods=['GET', 'POST'])
@login.login_required
def cancel():
    """Cancel tickets.

    Presents the user with a list of tickets, and upon form submission cancels
    the selected tickets, giving refunds as appropriate.
    """
    if request.method == 'POST':
        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(request.form.getlist('tickets[]'))
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
                    card_transactions[ticket.card_transaction_id]['tickets'] \
                        .append(ticket)
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
            flash(
                (
                    u'Some of your tickets could not be automatically '
                    u'refunded, and so were not cancelled. You can try again '
                    u'later, but if this problem continues to occur, you '
                    u'should contact <a href="{0}">the ticketing officer</a>'
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
                flash(
                    (
                        u'Some of the tickets you selected have been '
                        u'cancelled. See other messages for details.'
                    ),
                    'info'
                )
            else:
                flash(
                    u'All of the tickets you selected have been cancelled.',
                    'info'
                )

    return render_template('purchase/cancel.html')

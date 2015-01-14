# coding: utf-8
from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask.ext.login import login_required, current_user

from kebleball.app import app
from kebleball.database.ticket import Ticket
from kebleball.database.waiting import Waiting
from kebleball.database.card_transaction import CardTransaction
from kebleball.database import db
from kebleball.helpers.purchase import canBuy, canWait
from kebleball.helpers.validators import validateVoucher, validateReferrer

log = app.log_manager.log_purchase
log_event = app.log_manager.log_event

purchase = Blueprint('purchase', __name__)

@purchase.route('/purchase', methods=['GET','POST'])
@login_required
def purchaseHome():
    (buyingPermitted, ticketsAvailable, canBuyMessage) = canBuy(current_user)

    if not buyingPermitted:
        flash(
            u'You cannot currently purchase tickets, because ' + canBuyMessage,
            'info'
        )

        (waitingPermitted, waitingAvailable, canWaitMessage) = canWait(current_user)
        if waitingPermitted:
            flash(
                (
                    u'Please join the waiting list, and you will be allocated '
                    u'tickets as they become available'
                ),
                'info'
            )
            return redirect(url_for('purchase.wait'))
        else:
            return redirect(url_for('dashboard.dashboardHome'))

    if request.method == 'POST':
        valid = True
        flashes = []

        numTickets = int(request.form['numTickets'])

        if numTickets > ticketsAvailable:
            valid = False
            flashes.append(u'You cannot buy that many tickets')
        elif numTickets < 1:
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
        elif request.form['paymentMethod'] == 'Battels' and not current_user.canPayByBattels():
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
            (result, response, voucher) = validateVoucher(request.form['voucherCode'])
            if not result:
                valid = False
                flashes.append(response['message'] + u' Please clear the discount code field to continue without using a voucher.')

        referrer = None
        if 'referrerEmail' in request.form and request.form['referrerEmail'] != '':
            (result, response, referrer) = validateReferrer(request.form['referrerEmail'], current_user)
            if not result:
                valid = False
                flashes.append(response['message'] + u' Please clear the referrer field to continue without giving somebody credit.')

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
                'purchase/purchaseHome.html',
                form=request.form,
                numTickets=numTickets,
                canBuy=ticketsAvailable
            )

        tickets = []

        if current_user.getsDiscount():
            tickets.append(
                Ticket(
                    current_user,
                    request.form['paymentMethod'],
                    current_user.get_base_ticket_price() - app.config['KEBLE_DISCOUNT']
                )
            )
            start = 1
        else:
            start = 0

        for x in xrange(start, numTickets):
            tickets.append(
                Ticket(
                    current_user,
                    request.form['paymentMethod'],
                    current_user.get_base_ticket_price()
                )
            )

        if (
            request.form['paymentMethod'] == 'Cash' or
            request.form['paymentMethod'] == 'Cheque'
        ):
            for ticket in tickets:
                ticket.addNote(
                    request.form['paymentMethod'] +
                    ' payment reason: ' +
                    request.form['paymentReason']
                )

        if voucher is not None:
            (success, tickets, error) = voucher.apply(tickets, current_user)
            if not success:
                flash('Could not use Voucher - ' + error, 'error')

        if referrer is not None:
            for ticket in tickets:
                ticket.setReferrer(referrer)

        db.session.add_all(tickets)
        db.session.commit()

        log_event(
            'Purchased Tickets',
            tickets,
            current_user
        )

        expires = None
        for ticket in tickets:
            if (
                expires == None or
                ticket.expires < expires
            ):
                expires = ticket.expires

        totalValue = sum([ticket.price for ticket in tickets])

        flash(
            (
                u'{0} tickets have been reserved for you at a total cost of '
                u'&pound;{1:.2f}.'
            ).format(
                numTickets,
                totalValue / 100.0
            ),
            'success'
        )

        if totalValue > 0:
            flash(
                (
                    u'You must set a name on your tickets before they '
                    u'can be paid for. Please set names on your tickets '
                    u'and then click the "Complete Payment" button. '
                    u'You must complete payment for these '
                    u'tickets by {0}'
                ).format(
                    expires.strftime('%H:%M %d/%m/%Y')
                ),
                'info'
            )

        else:
            flash(u'Please set names for these tickets before collection', 'info')
        return redirect(url_for('dashboard.dashboardHome'))
    else:
        return render_template(
            'purchase/purchaseHome.html',
            canBuy=ticketsAvailable
        )

@purchase.route('/purchase/wait', methods=['GET','POST'])
@login_required
def wait():
    (waitingPermitted, waitingAvailable, canWaitMessage) = canWait(current_user)
    if not waitingPermitted:
        flash(
            (
                u'You cannot join the waiting list at this time because ' +
                canWaitMessage
            ),
            'info'
        )
        return redirect(url_for('dashboard.dashboardHome'))

    if request.method == 'POST':
        valid = True
        flashes = []

        numTickets = int(request.form['numTickets'])

        if numTickets > waitingAvailable:
            valid = False
            flashes.append(u'You cannot wait for that many tickets')
        elif numTickets < 1:
            valid = False
            flashes.append(u'You must wait for at least 1 ticket')

        if 'acceptTerms' not in request.form:
            valid = False
            flashes.append(u'You must accept the Terms and Conditions')

        referrer = None
        if 'referrerEmail' in request.form and request.form['referrerEmail'] != '':
            (result, response, referrer) = validateReferrer(request.form['referrerEmail'], current_user)
            if not result:
                valid = False
                flashes.append(response['message'] + u' Please clear the referrer field to continue without giving somebody credit.')

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
                'purchase/purchaseHome.html',
                form=request.form,
                numTickets=numTickets,
                canWait=waitingAvailable
            )

        db.session.add(
            Waiting(
                current_user,
                numTickets,
                referrer
            )
        )
        db.session.commit()

        log_event(
            'Joined waiting list for {0} tickets'.format(
                numTickets
            ),
            [],
            current_user
        )

        flash(
            (
                u'You have been added to the waiting list for {0} ticket{1}.'
            ).format(
                numTickets,
                '' if numTickets == 1 else 's'
            ),
            'success'
        )

        return redirect(url_for('dashboard.dashboardHome'))
    else:
        return render_template(
            'purchase/wait.html',
            canWait=waitingAvailable
        )

@purchase.route('/purchase/change-method', methods=['GET','POST'])
@login_required
def changeMethod():
    if request.method == 'POST':
        tickets = Ticket.query \
            .filter(Ticket.id.in_(request.form.getlist('tickets[]'))) \
            .filter(Ticket.owner_id == current_user.id) \
            .filter(Ticket.paid == False) \
            .all()

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
            flash(u'You must give a reason for paying by cash or cheque.', 'error')
            return render_template(
                'purchase/changeMethod.html',
                tickets=request.form.getlist('tickets[]')
            )
        elif 'paymentReason' in request.form:
            reason = request.form['paymentReason']
        else:
            reason = None

        for ticket in tickets:
            ticket.setPaymentMethod(request.form['paymentMethod'], reason)

        db.session.commit()

        log_event(
            'Changed Payment Method to {0}'.format(
                request.form['paymentMethod']
            ),
            tickets,
            current_user
        )

        flash(
            u'The payment method on the selected tickets has been changed successfully',
            'success'
        )

    return render_template('purchase/changeMethod.html')

@purchase.route('/purchase/card-confirm', methods=['GET','POST'])
@login_required
def cardConfirm():
    if request.method == 'POST':
        tickets = Ticket.query \
            .filter(Ticket.id.in_(request.form.getlist('tickets[]'))) \
            .filter(Ticket.owner_id == current_user.id) \
            .filter(Ticket.paid == False) \
            .all()

        while None in tickets:
            tickets.remove(None)

        transaction = CardTransaction(
            current_user,
            tickets
        )

        db.session.add(transaction)
        db.session.commit()

        ewayURL = transaction.getEwayURL()

        if ewayURL is not None:
            return redirect(ewayURL)

    return render_template('purchase/cardConfirm.html')

@purchase.route('/purchase/eway-success/<int:id>')
def ewaySuccess(id):
    transaction = CardTransaction.get_by_id(id)

    transaction.processEwayPayment()

    return redirect(url_for('dashboard.dashboardHome'))

@purchase.route('/purchase/eway-cancel/<int:id>')
def ewayCancel(id):
    transaction = CardTransaction.get_by_id(id)

    transaction.cancelEwayPayment()

    return redirect(url_for('dashboard.dashboardHome'))

@purchase.route('/purchase/battels-confirm', methods=['GET','POST'])
@login_required
def battelsConfirm():
    if not current_user.canPayByBattels():
        flash(
            u'You cannot currently pay by battels. Please change the payment '
            u'method on your tickets',
            'warning'
        )
        return redirect(url_for('purchase.changeMethod'))

    if request.method == 'POST':
        tickets = Ticket.query \
            .filter(Ticket.id.in_(request.form.getlist('tickets[]'))) \
            .filter(Ticket.owner_id == current_user.id) \
            .filter(Ticket.paid == False) \
            .all()

        while None in tickets:
            tickets.remove(None)

        if (
            app.config['CURRENT_TERM'] == 'HT' and
            request.form['paymentTerm'] != 'HT'
        ):
            flash(u'Invalid choice of payment term', 'warning')
        else:
            battels = current_user.battels

            for ticket in tickets:
                battels.charge(ticket, request.form['paymentTerm'])

            db.session.commit()

            log_event(
                'Confirmed battels payment',
                tickets,
                current_user
            )

            flash(u'Your battels payment has been confirmed','success')

    return render_template('purchase/battelsConfirm.html')

@purchase.route('/purchase/cancel', methods=['GET','POST'])
@login_required
def cancel():
    if request.method == 'POST':
        tickets = Ticket.query \
            .filter(Ticket.id.in_(request.form.getlist('tickets[]'))) \
            .filter(Ticket.owner_id == current_user.id) \
            .all()

        while None in tickets:
            tickets.remove(None)

        tickets = filter(
            (lambda x: x.canBeCancelledAutomatically()),
            tickets
        )

        cardTransactions = {}

        cancelled = []

        for ticket in tickets:
            if not ticket.paid:
                ticket.cancelled = True
                db.session.commit()
                cancelled.append(ticket)
            elif ticket.paymentmethod == 'Free':
                ticket.cancelled = True
                db.session.commit()
                cancelled.append(ticket)
            elif ticket.paymentmethod == 'Battels':
                ticket.battels.cancel(ticket)
                cancelled.append(ticket)
            elif ticket.paymentmethod == 'Card':
                if ticket.card_transaction_id in cardTransactions:
                    cardTransactions[ticket.card_transaction_id]['tickets'] \
                        .append(ticket)
                else:
                    cardTransactions[ticket.card_transaction_id] = {
                        'transaction': ticket.card_transaction,
                        'tickets': [ticket]
                    }

        refundFailed = False

        for transaction in cardTransactions.itervalues():
            value = sum([t.price for t in transaction['tickets']])

            if transaction['transaction'].processRefund(value):
                cancelled.extend(transaction['tickets'])
                for ticket in transaction['tickets']:
                    ticket.cancelled = True
                db.session.commit()
            else:
                refundFailed = True

        if refundFailed:
            flash(
                (
                    u'Some of your tickets could not be automatically '
                    u'refunded, and so were not cancelled. You can try again '
                    u'later, but if this problem continues to occur, you '
                    u'should contact <a href="{0}">the ticketing officer</a>'
                ).format(
                    app.config['TICKETS_EMAIL_LINK']
                ),
                'warning'
            )

        if len(cancelled) > 0:
            log_event(
                'Cancelled tickets',
                cancelled,
                current_user
            )

            if refundFailed:
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

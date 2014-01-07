# coding: utf-8
from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask.ext.login import login_required, fresh_login_required, current_user

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
    if request.method == 'POST':
        valid = True
        flashes = []

        numTickets = int(request.form['numTickets'])

        if numTickets > canBuy(current_user):
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
                canBuy=canBuy(current_user)
            )

        tickets = []

        if current_user.getsDiscount():
            tickets.append(
                Ticket(
                    current_user,
                    request.form['paymentMethod'],
                    app.config['TICKET_PRICE'] - app.config['KEBLE_DISCOUNT']
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
                    app.config['TICKET_PRICE']
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
                    u'Follow the instructions below to complete payment for '
                    u'these tickets (and any others you have reserved but '
                    u'not paid for). You must complete payment for these '
                    u'tickets by {0}'
                ).format(
                    expires.strftime('%H:%M %d/%m/%Y')
                ),
                'info'
            )

            if request.form['paymentMethod'] == 'Card':
                return redirect(url_for('purchase.cardConfirm'))
            elif request.form['paymentMethod'] == 'Battels':
                return redirect(url_for('purchase.battelsConfirm'))
            else:
                return redirect(url_for('purchase.cashChequeConfirm'))
        else:
            return redirect(url_for('dashboard.dashboardHome'))
    else:
        if canBuy(current_user) == 0:
            flash(
                (
                    u'There are no tickets currently available for Keble Ball. '
                    u'If you would like tickets for the Ball, please join the '
                    u'waiting list.'
                ),
                'info'
            )
            return redirect(url_for('purchase.wait'))
        return render_template(
            'purchase/purchaseHome.html',
            canBuy=canBuy(current_user)
        )

@purchase.route('/purchase/wait', methods=['GET','POST'])
@login_required
def wait():
    if request.method == 'POST':
        valid = True
        flashes = []

        numTickets = int(request.form['numTickets'])

        if numTickets > canWait(current_user):
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
                canWait=canWait(current_user)
            )

        db.session.add(
            Waiting(
                current_user,
                numTickets,
                referrer
            )
        )
        db.session.commit()

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
        if canWait(current_user) == 0:
            flash(
                (
                    u'You are currently unable to join the waiting list. '
                    u'Please try again later.'
                ),
                'info'
            )
            return redirect(url_for('dashboard.dashboardHome'))
        return render_template(
            'purchase/wait.html',
            canWait=canWait(current_user)
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
                tickets = request.form['tickets']
            )
        elif 'paymentReason' in request.form:
            reason = request.form['paymentReason']
        else:
            reason = None

        for ticket in tickets:
            ticket.setMethod(request.form['paymentMethod'], reason)

        db.session.commit()

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

        someCancelled = False

        for ticket in tickets:
            if not ticket.paid:
                ticket.cancelled = True
                someCancelled = True
            elif ticket.paymentmethod == 'Free':
                ticket.cancelled = True
                someCancelled = True
            elif ticket.paymentmethod == 'Battels':
                ticket.battels.cancel(ticket)
                someCancelled = True
            elif ticket.paymentmethod == 'Card':
                if ticket.card_transaction_id in cardTransactions:
                    cardTransactions[ticket.card_transaction_id]['tickets'] \
                        .append(ticket)
                else:
                    cardTransactions[ticket.card_transaction_id] = {
                        'transaction': ticket.card_transaction,
                        'tickets': [ticket]
                    }

        #raise Exception

        refundFailed = False

        for transaction in cardTransactions.itervalues():
            value = sum([t.price for t in transaction['tickets']])

            if transaction['transaction'].processRefund(value):
                someCancelled = True
                for ticket in tickets:
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

        if someCancelled:
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

        db.session.commit()

    return render_template('purchase/cancel.html')
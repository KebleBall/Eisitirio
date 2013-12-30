from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask.ext.login import login_required, fresh_login_required, current_user

from kebleball.app import app
from kebleball.database.ticket import Ticket
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
                canBuy=canBuy(current_user),
                canWait=canWait(current_user)
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
                u'&pound;{1}.'
            ).format(
                numTickets,
                totalValue
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
        return render_template(
            'purchase/purchaseHome.html',
            canBuy=canBuy(current_user),
            canWait=canWait(current_user)
        )



@purchase.route('/purchase/change-method')
@login_required
def changeMethod():
    # [todo] - Add changeMethod
    raise NotImplementedError('changeMethod')

@purchase.route('/purchase/card-confirm')
@login_required
def cardConfirm():
    # [todo] - Add cardConfirm
    raise NotImplementedError('cardConfirm')

@purchase.route('/purchase/eway-callback')
@login_required
def ewayCallback():
    # [todo] - Add ewayCallback
    raise NotImplementedError('ewayCallback')

@purchase.route('/purchase/battels-confirm')
@login_required
def battelsConfirm():
    # [todo] - Add battelsConfirm
    raise NotImplementedError('battelsConfirm')

@purchase.route('/purchase/cash-cheque-confirm')
@login_required
def cashChequeConfirm():
    # [todo] - Add cashChequeConfirm
    raise NotImplementedError('cashChequeConfirm')

@purchase.route('/purchase/resell')
@fresh_login_required
def resell():
    # [todo] - Add resell
    raise NotImplementedError('resell')

@purchase.route('/purchase/cancel')
@fresh_login_required
def cancel():
    # [todo] - Add cancel
    raise NotImplementedError('cancel')
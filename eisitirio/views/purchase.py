# coding: utf-8
"""Views related to the purchase process."""

from __future__ import unicode_literals

from flask.ext import login
import flask
from sqlalchemy import or_

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import validators
from eisitirio.helpers import login_manager
from eisitirio.logic import cancellation_logic
from eisitirio.logic import realex_logic
from eisitirio.logic import purchase_logic
from eisitirio.logic import payment_logic
from eisitirio.logic.custom_logic import ticket_logic

APP = app.APP
DB = db.DB

PURCHASE = flask.Blueprint('purchase', __name__)

@PURCHASE.route('/purchase', methods=['GET', 'POST'])
@login.login_required
def purchase_home():
    """First step of the purchasing flow.

    Checks if the user can purchase tickets, and processes the purchase form.
    """
    if login.current_user.purchase_group:
        if login.current_user == login.current_user.purchase_group.leader:
            if APP.config['TICKETS_ON_SALE']:
                return flask.redirect(flask.url_for('group_purchase.checkout'))
            else:
                flask.flash(
                    (
                        'You cannot currently purchase tickets because you are '
                        'leading a purchase group. You will be able to '
                        'purchase tickets on behalf of your group when general '
                        'release starts.'
                    ),
                    'info'
                )
                return flask.redirect(flask.url_for('dashboard.dashboard_home'))
        else:
            flask.flash(
                (
                    'You cannot currently purchase tickets because you are a '
                    'member of a purchase group. Your group leader {0} will be '
                    'able to purchase tickets on behalf of your group when '
                    'general release starts.'
                ).format(login.current_user.purchase_group.leader.full_name),
                'info'
            )
            return flask.redirect(flask.url_for('dashboard.dashboard_home'))

    ticket_info = purchase_logic.get_ticket_info(
        login.current_user
    )
    if models.Waiting.query.count() > 0 or not ticket_info.ticket_types:
        flask.flash(
            'You are not able to purchase tickets at this time.',
            'info'
        )

        if purchase_logic.wait_available(login.current_user):
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

    if flask.request.method == 'POST':
        for ticket_type, _ in ticket_info.ticket_types:
            num_tickets[ticket_type.slug] = int(
                flask.request.form['num_tickets_{0}'.format(ticket_type.slug)]
            )

        flashes = purchase_logic.validate_tickets(
            ticket_info,
            num_tickets
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
                num_tickets=num_tickets,
                ticket_info=ticket_info
            )


        tickets = purchase_logic.create_tickets(
            login.current_user,
            ticket_info,
            num_tickets
        )

        if voucher is not None:
            (success, tickets, error) = voucher.apply(tickets,
                                                      login.current_user)
            if not success:
                flask.flash('Could not use voucher - ' + error, 'error')


        roundup_price = purchase_logic.check_roundup_donation(flashes)

        if roundup_price is not 0:
            roundup_donation = None

            roundup_donation = models.RoundupDonation(
                    roundup_price,
                    login.current_user,
            )

            if roundup_donation is not None:
                # Tack on the roundup donation fee to their ticket(s)
                # Entry
                tickets = roundup_donation.apply(tickets)
                DB.session.add(roundup_donation);


        DB.session.add_all(tickets)
        DB.session.commit()

        APP.log_manager.log_event(
            'Purchased Tickets',
            tickets=tickets,
            user=login.current_user
        )

        # return flask.render_template(
        #    'purchase/purchase_home.html',
        #    num_tickets=num_tickets,
        #    ticket_info=ticket_info
        # )
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
            ticket_info=ticket_info
        )

@PURCHASE.route('/purchase/upgrade', methods=['GET', 'POST'])
@login.login_required
def upgrade_ticket():
    """Buy an upgrade ticket

    Checks if the user can purchase tickets, and processes the purchase form.
    """

    price_per_ticket, number_upgrade = purchase_logic.get_ticket_info_for_upgrade(login.current_user)

    if number_upgrade <= 0 or not ticket_logic.can_buy_upgrade(login.current_user):
        flask.flash(
            'You are not able to upgrade tickets at this time.',
            'info'
        )
        return flask.redirect(flask.url_for('dashboard.dashboard_home'))


    if flask.request.method == 'POST':
        selected_tickets = flask.request.form.getlist('tickets[]')
        if not selected_tickets:
            flask.flash(
                'Please select the tickets you want to upgrade.',
                'info'
            )
            return flask.redirect(flask.url_for('purchase.upgrade_tickets'))

        total_amt = price_per_ticket * len(selected_tickets)

        admin_fee = models.AdminFee(
            total_amt,
            "Ticket Upgrade: {0}".format(','.join(selected_tickets)),
            login.current_user,
            login.current_user
        )

        APP.log_manager.log_event(
            'Upgraded Tickets: {0}'.format(', '.join(selected_tickets)),
            admin_fee=admin_fee,
            user=login.current_user
        )

        DB.session.add(admin_fee)
        DB.session.commit()

        return payment_logic.pay_admin_fee(admin_fee, 'Card', 'HT')

    return flask.render_template('purchase/upgrade.html')

@PURCHASE.route('/purchase/wait', methods=['GET', 'POST'])
@login.login_required
def wait():
    """Handles joining the waiting list.

    Checks if the user can join the waiting list, and processes the form to
    create the requisite waiting list entry.
    """
    wait_available = purchase_logic.wait_available(login.current_user)

    if not wait_available:
        flask.flash('You cannot join the waiting list at this time.', 'info')

        return flask.redirect(flask.url_for('dashboard.dashboard_home'))

    if flask.request.method != 'POST':
        return flask.render_template(
            'purchase/wait.html',
            wait_available=wait_available
        )

    flashes = []

    num_tickets = int(flask.request.form['num_tickets'])

    if num_tickets > wait_available:
        flashes.append('You cannot wait for that many tickets')
    elif num_tickets < 1:
        flashes.append('You must wait for at least 1 ticket')

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
            'purchase/wait.html',
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
        user=login.current_user
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

@PURCHASE.route('/purchase/complete-payment', methods=['GET', 'POST'])
@login.login_required
def complete_payment():
    """Allow the user to complete payment for tickets.

    Used if card payment fails, or for manually allocated tickets.
    """
    if flask.request.method == 'POST':
        flashes = []

        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(flask.request.form.getlist('tickets[]'))
        ).filter(
            models.Ticket.owner_id == login.current_user.object_id
        ).filter(
            models.Ticket.paid == False # pylint: disable=singleton-comparison
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

@PURCHASE.route('/purchase/cancel', methods=['GET', 'POST'])
@login.login_required
def cancel():
    """Allow the user to cancel tickets."""
    if flask.request.method == 'POST':
        cancellation_logic.cancel_tickets(
            login.current_user.active_tickets.filter(
                models.Ticket.object_id.in_(
                    flask.request.form.getlist('tickets[]')
                )
            ).all()
        )

    return flask.render_template('purchase/cancel.html')

@PURCHASE.route('/resell', methods=['GET', 'POST'])
@login.login_required
def resell():
    """Allow the user to resell tickets.

    Resell here actually means that the reseller's tickets will be cancelled,
    and new tickets created in the account of the recipient.
    """
    if flask.request.method != 'POST':
        return flask.render_template('purchase/resell.html')

    tickets = login.current_user.active_tickets.filter(
        models.Ticket.object_id.in_(flask.request.form.getlist('tickets[]'))
    ).all()

    resell_to = models.User.get_by_email(flask.request.form['resell_to'])

    flashes = []

    if not tickets:
        flashes.append("You haven't selected any tickets.")

    if not resell_to:
        flashes.append('No user with that email exists')
    elif resell_to == login.current_user:
        flashes.append('You can\'t resell tickets to yourself')

    if flashes:
        for flash in flashes:
            flask.flash(flash, 'error')

        return flask.render_template('purchase/resell.html')

    if cancellation_logic.cancel_tickets(tickets, quiet=True):
        found_uncancelled = False

        new_tickets = []

        ticket_type = APP.config['DEFAULT_TICKET_TYPE']

        for ticket in tickets:
            if ticket.cancelled:
                new_tickets.append(models.Ticket(
                    resell_to,
                    ticket_type.slug,
                    ticket_type.price
                ))
            else:
                found_uncancelled = True

        DB.session.add_all(new_tickets)
        DB.session.commit()

        APP.email_manager.send_template(
            resell_to.email,
            'You have been resold tickets',
            'resale.email',
            reseller=login.current_user,
            resell_to=resell_to,
            num_tickets=len(new_tickets),
            expiry=new_tickets[0].expires
        )

        APP.log_manager.log_event(
            'Cancelled tickets for resale',
            tickets=tickets,
            user=login.current_user
        )

        APP.log_manager.log_event(
            'Created tickets from resale',
            tickets=new_tickets,
            user=resell_to
        )

        if found_uncancelled:
            flask.flash('The resale was partially successful.', 'success')
            flask.flash(
                (
                    'Some of your tickets could not be automatically '
                    'cancelled, and so could not be resold. You can try again '
                    'later, but if this problem continues to occur, you should '
                    'contact <a href="{0}">the ticketing officer</a>'
                ).format(
                    APP.config['TICKETS_EMAIL_LINK']
                ),
                'warning'
            )
        else:
            flask.flash('The resale was successful.', 'success')
    else:
        flask.flash(
            (
                'None of your tickets could be automatically cancelled, and so '
                'they could not be resold. You can try again later, but if '
                'this problem continues to occur, you should contact '
                '<a href="{0}">the ticketing officer</a>'
            ).format(
                APP.config['TICKETS_EMAIL_LINK']
            ),
            'error'
        )

    return flask.render_template('purchase/resell.html')

@PURCHASE.route('/purchase/postage', methods=['GET', 'POST'])
@login.login_required
def buy_postage():
    """Allow the user to buy postage for tickets."""
    if flask.request.method == 'POST':
        flashes = []

        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(flask.request.form.getlist('tickets[]'))
        ).filter(
            models.Ticket.cancelled == False # pylint: disable=singleton-comparison
        ).filter(or_(
            models.Ticket.owner == login.current_user,
            models.Ticket.holder == login.current_user
        )).all()

        if not tickets:
            flashes.append(
                'You have not selected any tickets to buy postage for.'
            )

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
                'purchase/buy_postage.html',
                form=flask.request.form
            )

        return payment_logic.buy_postage(
            tickets,
            postage,
            method,
            term,
            address
        )

    return flask.render_template('purchase/buy_postage.html')

@PURCHASE.route(
    '/purchase/admin_fee/<int:admin_fee_id>',
    methods=['GET', 'POST']
)
@login.login_required
def pay_admin_fee(admin_fee_id):
    """Allow the user to pay an admin fee."""
    admin_fee = models.AdminFee.get_by_id(admin_fee_id)

    if not admin_fee:
        flask.flash('Admin Fee not found', 'warning')
    elif admin_fee.charged_to != login.current_user:
        flask.flash('That is not your admin fee to pay.', 'warning')
    elif admin_fee.paid:
        flask.flash('That admin fee has been paid.', 'warning')
    else:
        if flask.request.method == 'POST':
            flashes = []

            payment_method, payment_term = purchase_logic.check_payment_method(
                flashes
            )

            if flashes:
                flask.flash(
                    (
                        'There were errors in your input. Please fix '
                        'these and try again'
                    ),
                    'error'
                )
                for msg in flashes:
                    flask.flash(msg, 'warning')

                return flask.render_template(
                    'purchase/pay_admin_fee.html',
                    fee=admin_fee
                )

            return payment_logic.pay_admin_fee(admin_fee, payment_method,
                                               payment_term)
        else:
            return flask.render_template(
                'purchase/pay_admin_fee.html',
                fee=admin_fee
            )

    return flask.redirect(flask.request.referrer or
                          flask.url_for('dashboard.dashboard_home'))

@PURCHASE.route('/purchase/payment-interstitial/<int:transaction_id>', methods=['GET'])
@login.login_required
def payment_interstitial(transaction_id):
    form = realex_logic.generate_payment_form(
        models.Transaction.get_by_id(transaction_id)
    )
    return flask.render_template('purchase/payment_interstitial.html', form=form)

@PURCHASE.route('/purchase/payment-processed', methods=['GET','POST'])
def payment_processed():
    """Callback from realex. Data received in a POST request, see the
    Realex website for details on how the data is structured. This records
    the end result of the transaction in the database (using
    'process_payment') and then redirects the user to their dashboard.
    Errors and warnings are recorded using flask.flash inside of
    process_payment."""
    if flask.request.method == 'POST':
        response = realex_logic.process_payment(flask.request)
        return flask.render_template('purchase/payment_processed.html')
        # return flask.redirect(flask.url_for('dashboard.dashboard_home'))
    else:
        return flask.render_template('purchase/payment_processed.html')
        # return flask.redirect(flask.url_for('dashboard.dashboard_home'))

@PURCHASE.route('/purchase/verify-ticket/<int:ticket_id>')
def api_verify_ticket(ticket_id):
    ticket = models.Ticket.get_by_id(ticket_id)

    print ticket

    if ticket is not None:
        return "true"
    else:
        return "false"

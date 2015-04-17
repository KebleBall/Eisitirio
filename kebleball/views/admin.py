# coding: utf-8
"""Views related to administrative tasks."""

from __future__ import unicode_literals

import csv
import datetime
import re
import StringIO

from dateutil import parser
from flask.ext import login
import flask
import sqlalchemy

from kebleball import app
from kebleball import helpers
from kebleball.database import db
from kebleball.database import models
from kebleball.helpers import login_manager
from kebleball.helpers import statistic_plots

APP = app.APP
DB = db.DB

ADMIN = flask.Blueprint('admin', __name__)

@ADMIN.route('/admin', methods=['GET', 'POST'])
@ADMIN.route('/admin/page/<int:page>', methods=['GET', 'POST'])
@login_manager.admin_required
def admin_home(page=1):
    """Admin homepage, search for users, tickets or log entries.

    Displays a form with lots of filters on users, tickets and log entries. On
    submission, generates a filtered query for each of users, tickets and log
    entries, and appropriately joins them to return the results of the requested
    type.
    """
    results = None
    category = None
    form = {}

    if flask.request.method == 'POST':
        user_query = models.User.query
        has_user_filter = False
        ticket_query = models.Ticket.query
        has_ticket_filter = False
        log_query = models.Log.query
        has_log_filter = False

        num_per_page = int(flask.request.form['num_results'])
        form = flask.request.form

        if (
                'user_name' in flask.request.form and
                flask.request.form['user_name'] != ''
        ):
            user_query = user_query.filter(
                models.User.full_name.like(
                    '%' + flask.request.form['user_name'] + '%'
                )
            )
            has_user_filter = True

        if (
                'user_email' in flask.request.form and
                flask.request.form['user_email'] != ''
        ):
            user_query = user_query.filter(
                models.User.email == flask.request.form['user_email'])
            has_user_filter = True

        if (
                'user_college' in flask.request.form and
                flask.request.form['user_college'] != '' and
                flask.request.form['user_college'] != 'Any'
        ):
            user_query = user_query.filter(
                models.User.college_id ==
                flask.request.form['user_college']
            )
            has_user_filter = True

        if (
                'user_affiliation' in flask.request.form and
                flask.request.form['user_affiliation'] != '' and
                flask.request.form['user_affiliation'] != 'Any'
        ):
            user_query = user_query.filter(
                models.User.affiliation_id ==
                flask.request.form['user_affiliation']
            )
            has_user_filter = True

        if (
                'user_tickets' in flask.request.form and
                flask.request.form['user_tickets'] != '' and
                flask.request.form['user_tickets'] != 'Any'
        ):
            if flask.request.form['user_tickets'] == 'Has':
                user_query = user_query.filter(models.User.tickets.any())
            else:
                user_query = user_query.filter(~models.User.tickets.any())
            has_user_filter = True

        if (
                'user_waiting' in flask.request.form and
                flask.request.form['user_waiting'] != '' and
                flask.request.form['user_waiting'] != 'Any'
        ):
            if flask.request.form['user_waiting'] == 'Is':
                user_query = user_query.filter(models.User.waiting.any())
            else:
                user_query = user_query.filter(~models.User.waiting.any())
            has_user_filter = True

        if (
                'ticket_number' in flask.request.form and
                flask.request.form['ticket_number'] != ''
        ):
            ticket_query = ticket_query.filter(
                models.Ticket.object_id == flask.request.form['ticket_number']
            )
            has_ticket_filter = True

        if (
                'ticket_name' in flask.request.form and
                flask.request.form['ticket_name'] != ''
        ):
            ticket_query = ticket_query.filter(
                models.Ticket.name.like(
                    '%' + flask.request.form['ticket_name'] + '%'
                )
            )
            has_ticket_filter = True

        if (
                'ticket_barcode' in flask.request.form and
                flask.request.form['ticket_barcode'] != ''
        ):
            ticket_query = ticket_query.filter(
                models.Ticket.barcode == flask.request.form['ticket_barcode']
            )
            has_ticket_filter = True

        if (
                'ticket_min_price' in flask.request.form and
                flask.request.form['ticket_min_price'] != ''
        ):
            ticket_query = ticket_query.filter(
                models.Ticket.price >= flask.request.form['ticket_min_price']
            )
            has_ticket_filter = True

        if (
                'ticket_max_price' in flask.request.form and
                flask.request.form['ticket_max_price'] != ''
        ):
            ticket_query = ticket_query.filter(
                models.Ticket.price <= flask.request.form['ticket_max_price']
            )
            has_ticket_filter = True

        if (
                'ticket_method' in flask.request.form and
                flask.request.form['ticket_method'] != '' and
                flask.request.form['ticket_method'] != 'Any'
        ):
            ticket_query = ticket_query.filter(
                models.Ticket.payment_method ==
                flask.request.form['ticket_method']
            )
            has_ticket_filter = True

        if (
                'ticket_paid' in flask.request.form and
                flask.request.form['ticket_paid'] != '' and
                flask.request.form['ticket_paid'] != 'Any'
        ):
            ticket_query = ticket_query.filter(
                models.Ticket.paid ==
                (flask.request.form['ticket_paid'] == 'Is')
            )
            has_ticket_filter = True

        if (
                'ticket_collected' in flask.request.form and
                flask.request.form['ticket_collected'] != '' and
                flask.request.form['ticket_collected'] != 'Any'
        ):
            ticket_query = ticket_query.filter(
                models.Ticket.collected ==
                (flask.request.form['ticket_collected'] == 'Is')
            )
            has_ticket_filter = True

        if (
                'ticket_referrer' in flask.request.form and
                flask.request.form['ticket_referrer'] != '' and
                flask.request.form['ticket_referrer'] != 'Any'
        ):
            if flask.request.form['ticket_referrer'] == 'Has':
                ticket_query = ticket_query.filter(
                    models.Ticket.referrer_id != None
                )
            else:
                ticket_query = ticket_query.filter(
                    models.Ticket.referrer_id == None
                )
            has_ticket_filter = True

        if (
                'log_ip' in flask.request.form and
                flask.request.form['log_ip'] != ''
        ):
            log_query = log_query.filter(
                models.Log.ip == flask.request.form['log_ip']
            )
            has_log_filter = True

        if (
                'log_start' in flask.request.form and
                flask.request.form['log_start'] != ''
        ):
            try:
                dtstamp = parser.parse(flask.request.form['log_start'])
                log_query = log_query.filter(models.Log.timestamp >= dtstamp)
                has_log_filter = True
            except (ValueError, TypeError) as _:
                flask.flash(
                    'Could not parse start date/time, ignoring.',
                    'warning'
                )

        if (
                'log_end' in flask.request.form and
                flask.request.form['log_end'] != ''
        ):
            try:
                dtstamp = parser.parse(flask.request.form['log_end'])
                log_query = log_query.filter(models.Log.timestamp <= dtstamp)
                has_log_filter = True
            except (ValueError, TypeError) as _:
                flask.flash(
                    'Could not parse end date/time, ignoring.',
                    'warning'
                )

        if (
                'log_message' in flask.request.form and
                flask.request.form['log_message'] != ''
        ):
            log_query = log_query.filter(
                models.Log.action.like(
                    '%' + flask.request.form['log_message'] + '%'
                )
            )
            has_log_filter = True

        log_query = log_query.order_by(models.Log.timestamp.desc())

        if flask.request.form['search'] == 'user':
            if has_ticket_filter:
                user_query = user_query.join(
                    ticket_query.subquery(),
                    models.User.tickets
                )

            if has_log_filter:
                if flask.request.form['log_user'] == 'Actor':
                    user_query = user_query.join(
                        log_query.subquery(),
                        models.User.actions
                    )
                else:
                    user_query = user_query.join(
                        log_query.subquery(),
                        models.User.events
                    )

            results = user_query.paginate(page, num_per_page)
            category = 'User'
        elif flask.request.form['search'] == 'ticket':
            if has_user_filter:
                ticket_query = ticket_query.join(
                    user_query.subquery(),
                    models.Ticket.owner
                )

            if has_log_filter:
                ticket_query = ticket_query.join(
                    log_query.subquery(),
                    models.Ticket.log_entries
                )

            results = ticket_query.paginate(page, num_per_page)
            category = 'Ticket'
        elif flask.request.form['search'] == 'log':
            if has_user_filter:
                if flask.request.form['log_user'] == 'Actor':
                    log_query = log_query.join(
                        user_query.subquery(),
                        models.Log.actor
                    )
                else:
                    log_query = log_query.join(
                        user_query.subquery(),
                        models.Log.user
                    )

            if has_ticket_filter:
                log_query = log_query.join(
                    ticket_query.subquery(),
                    models.Log.tickets
                )

            results = log_query.paginate(page, num_per_page)
            category = 'Log'

    return flask.render_template(
        'admin/admin_home.html',
        form=form,
        colleges=models.College.query.all(),
        affiliations=models.Affiliation.query.all(),
        results=results,
        category=category
    )

@ADMIN.route('/admin/log/<int:entry_id>/view')
@login_manager.admin_required
def view_log(entry_id):
    """View a log entry."""
    log = models.Log.get_by_id(entry_id)

    return flask.render_template(
        'admin/view_log.html',
        log=log
    )

@ADMIN.route('/admin/transaction/<int:transaction_id>/view')
@ADMIN.route('/admin/transaction/<int:transaction_id>/view/page/<int:events_page>')
@login_manager.admin_required
def view_transaction(transaction_id, events_page=1):
    """View a card transaction object."""
    transaction = models.CardTransaction.get_by_id(transaction_id)

    if transaction:
        events = transaction.events.paginate(
            events_page,
            10,
            True
        )
    else:
        events = None

    return flask.render_template(
        'admin/view_transaction.html',
        transaction=transaction,
        events=events,
        events_page=events_page
    )

@ADMIN.route('/admin/transaction/<int:transaction_id>/refund',
             methods=['GET', 'POST'])
@login_manager.admin_required
def refund_transaction(transaction_id):
    """Refund a transaction.

    Allows part or full refunds for whatever reason, sends a request to eWay to
    refund money back to the user's card.
    """
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

    transaction = models.CardTransaction.get_by_id(transaction_id)

    if transaction:
        amount = (int(flask.request.form['refund_amount_pounds'])
                  * 100 + int(flask.request.form['refund_amount_pence']))

        if amount > (transaction.get_value() - transaction.refunded):
            flask.flash(
                'Cannot refund more than has been charged.',
                'warning'
            )
            return flask.redirect(
                flask.request.referrer or
                flask.url_for('admin.view_transaction',
                              transaction_id=transaction.transaction_id)
            )

        result = transaction.process_refund(amount)

        if not result:
            flask.flash(
                'Could not process refund.',
                'warning'
            )
        else:
            flask.flash(
                'Refund processed successfully.',
                'success'
            )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.view_transaction',
                                            transaction_id=transaction.transaction_id))
    else:
        flask.flash(
            'Could not find transaction, could not cancel.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN.route('/admin/statistics')
@login_manager.admin_required
def statistics():
    """Display statistics about the ball.

    Computes a number of statistics about the ball (live), and displays them
    alongside graphs.
    """
    total_value = DB.session.query(
        sqlalchemy.func.sum(models.Ticket.price)
    ).filter(
        models.Ticket.cancelled != True
    ).scalar()

    if total_value is None:
        total_value = 0

    paid_value = DB.session.query(
        sqlalchemy.func.sum(models.Ticket.price)
    ).filter(
        models.Ticket.paid == True
    ).filter(
        models.Ticket.cancelled != True
    ).scalar()

    if paid_value is None:
        paid_value = 0

    cancelled_value = DB.session.query(
        sqlalchemy.func.sum(models.Ticket.price)
    ).filter(
        models.Ticket.cancelled == True
    ).scalar()

    if cancelled_value is None:
        cancelled_value = 0

    payment_method_values = DB.session.query(
        sqlalchemy.func.sum(models.Ticket.price), models.Ticket.payment_method
    ).filter(
        models.Ticket.cancelled != True
    ).group_by(
        models.Ticket.payment_method
    ).all()

    return flask.render_template(
        'admin/statistics.html',
        total_value=total_value,
        paid_value=paid_value,
        cancelled_value=cancelled_value,
        payment_method_values=payment_method_values
    )

@ADMIN.route('/admin/announcements', methods=['GET', 'POST'])
@ADMIN.route('/admin/announcements/page/<int:page>', methods=['GET', 'POST'])
@login_manager.admin_required
def announcements(page=1):
    """Manage announcements.

    Allows the creation of announcements, viewing and deleting existing
    announcements, and cancelling email sending for existing announcements.
    """
    form = {}

    if flask.request.method == 'POST':
        form = flask.request.form

        success = True

        if 'subject' not in form or form['subject'] == '':
            flask.flash(
                'Subject must not be blank',
                'warning'
            )
            success = False

        if 'message' not in form or form['message'] == '':
            flask.flash(
                'Message must not be blank',
                'warning'
            )
            success = False

        if 'tickets' in form and form['tickets'] == 'no':
            if 'collected' in form and form['collected'] == 'yes':
                flask.flash(
                    (
                        'A person cannot have no tickets and have collected '
                        'tickets'
                    ),
                    'warning'
                )
                success = False
            if 'uncollected' in form and form['uncollected'] == 'yes':
                flask.flash(
                    (
                        'A person cannot have no tickets and have uncollected '
                        'tickets'
                    ),
                    'warning'
                )
                success = False

        if success:
            college = None
            if 'college' in form and form['college'] != 'any':
                college = int(form['college'])

            affiliation = None
            if 'affiliation' in form and form['affiliation'] != 'any':
                affiliation = int(form['affiliation'])

            has_tickets = None
            if 'tickets' in form:
                if form['tickets'] == 'yes':
                    has_tickets = True
                elif form['tickets'] == 'no':
                    has_tickets = False

            is_waiting = None
            if 'waiting' in form:
                if form['waiting'] == 'yes':
                    is_waiting = True
                elif form['waiting'] == 'no':
                    is_waiting = False

            has_collected = None
            if 'collected' in form:
                if form['collected'] == 'yes':
                    has_collected = True
                elif form['collected'] == 'no':
                    has_collected = False

            has_uncollected = None
            if 'uncollected' in form:
                if form['uncollected'] == 'yes':
                    has_uncollected = True
                elif form['uncollected'] == 'no':
                    has_uncollected = False

            send_email = 'send_emails' in form and form['send_emails'] == 'yes'

            announcement = models.Announcement(
                form['subject'],
                form['message'],
                login.current_user.object_id,
                send_email,
                college,
                affiliation,
                has_tickets,
                is_waiting,
                has_collected,
                has_uncollected
            )

            DB.session.add(announcement)
            DB.session.commit()

            flask.flash(
                'Announcement created successfully',
                'success'
            )

            form = {}

    return flask.render_template(
        'admin/announcements.html',
        colleges=models.College.query.all(),
        affiliations=models.Affiliation.query.all(),
        announcements=models.Announcement.query.paginate(page, 10, False),
        form=form
    )

@ADMIN.route('/admin/announcement/<int:announcement_id>/delete')
@login_manager.admin_required
def delete_announcement(announcement_id):
    """Delete an announcement.

    Removes an announcement from the database, but cannot recall any emails
    which have already been sent
    """
    announcement = models.Announcement.get_by_id(announcement_id)

    if announcement:
        DB.session.delete(announcement)
        DB.session.commit()

        flask.flash(
            'Announcement deleted successfully',
            'success'
        )
    else:
        flask.flash(
            'Could not find announcement, could not delete',
            'warning'
        )

    return flask.redirect(flask.request.referrer or
                          flask.url_for('admin.announcements'))

@ADMIN.route('/admin/announcement/<int:announcement_id>/cancel')
@login_manager.admin_required
def cancel_announcement_emails(announcement_id):
    """Cancel sending emails for an announcement.

    Remove from the sending queue any pending emails for an announcement. Does
    not recall previously sent emails.
    """
    announcement = models.Announcement.get_by_id(announcement_id)

    if announcement:
        announcement.emails = []
        announcement.send_email = False
        DB.session.commit()

        flask.flash(
            'Announcement emails cancelled successfully',
            'success'
        )
    else:
        flask.flash(
            'Could not find announcement, could not cancel emails',
            'warning'
        )

    return flask.redirect(flask.request.referrer or
                          flask.url_for('admin.announcements'))

@ADMIN.route('/admin/vouchers', methods=['GET', 'POST'])
@ADMIN.route('/admin/vouchers/page/<int:page>', methods=['GET', 'POST'])
@login_manager.admin_required
def vouchers(page=1):
    """Manage vouchers.

    Handles the creation of discount vouchers, and allows their deletion.
    """
    form = {}

    if flask.request.method == 'POST':
        form = flask.request.form

        success = True

        expires = None

        if 'expires' in form and form['expires'] != '':
            try:
                expires = parser.parse(form['expires'])
                if expires < datetime.datetime.utcnow():
                    flask.flash(
                        'Expiry date cannot be in the past',
                        'warning'
                    )
                    success = False
            except (KeyError, ValueError) as _:
                flask.flash(
                    'Could not parse expiry date',
                    'warning'
                )
                success = False

        if 'voucher_type' not in form or form['voucher_type'] == '':
            flask.flash(
                'You must select a discout type',
                'warning'
            )
            success = False
        elif form['voucher_type'] == 'Fixed Price':
            value = (int(form['fixed_price_pounds'])
                     * 100 + int(form['fixed_price_pence']))
        elif form['voucher_type'] == 'Fixed Discount':
            value = (int(form['fixed_discount_pounds'])
                     * 100 + int(form['fixed_discount_pence']))
        else:
            value = int(form['fixed_discount'])
            if value > 100:
                flask.flash(
                    'Cannot give greater than 100% discount',
                    'warning'
                )
                success = False

        if not re.match('[a-zA-Z0-9]+', form['voucher_prefix']):
            flask.flash(
                (
                    'Voucher prefix must be non-empty and contain only '
                    'letters and numbers'
                ),
                'warning'
            )
            success = False

        if success:
            num_vouchers = int(form['num_vouchers'])
            single_use = 'single_use' in form and form['single_use'] == 'yes'

            for _ in xrange(num_vouchers):
                key = helpers.generate_key(10)
                voucher = models.Voucher(
                    '{0}-{1}'.format(
                        form['voucher_prefix'],
                        key
                    ),
                    expires,
                    form['voucher_type'],
                    value,
                    form['applies_to'],
                    single_use
                )
                DB.session.add(voucher)

            DB.session.commit()

            flask.flash(
                'Voucher(s) created successfully',
                'success'
            )

            form = {}

    voucher_query = models.Voucher.query

    if 'search' in flask.request.args:
        voucher_query = voucher_query.filter(
            models.Voucher.code.like(
                '%{0}%'.format(
                    flask.request.args['search']
                )
            )
        )

    voucher_results = voucher_query.paginate(
        page,
        10
    )

    return flask.render_template(
        'admin/vouchers.html',
        form=form,
        vouchers=voucher_results
    )

@ADMIN.route('/admin/voucher/<int:voucher_id>/delete')
@login_manager.admin_required
def delete_voucher(voucher_id):
    """Delete a discount voucher."""
    voucher = models.Voucher.get_by_id(voucher_id)

    if voucher:
        DB.session.delete(voucher)
        DB.session.commit()
        flask.flash(
            'Voucher deleted successfully',
            'success'
        )
    else:
        flask.flash(
            'Could not find voucher to delete',
            'warning'
        )

    return flask.redirect(flask.request.referrer or
                          flask.url_for('admin.vouchers'))

@ADMIN.route('/admin/waiting/<int:entry_id>/delete')
@login_manager.admin_required
def delete_waiting(entry_id):
    """Delete an entry from the waiting list."""
    waiting = models.Waiting.get_by_id(entry_id)

    if waiting:
        DB.session.delete(waiting)
        DB.session.commit()
        flask.flash(
            'Waiting list entry deleted',
            'success'
        )
    else:
        flask.flash(
            'Waiting list entry not found, could not delete.',
            'error'
        )

    return flask.redirect(flask.request.referrer or
                          flask.url_for('admin.admin_home'))

@ADMIN.route('/admin/graphs/sales')
@login_manager.admin_required
def graph_sales():
    """Render a graph showing sales statistics

    Shows statistics for number of tickets Available, Ordered, Paid, Collected,
    and Cancelled, plus the length of the waiting list.
    """
    return statistic_plots.create_plot('Sales')

@ADMIN.route('/admin/graphs/colleges')
@login_manager.admin_required
def graph_colleges():
    """Render graph showing statistics on users' colleges.

    Shows how many users are registered from each college.
    """
    return statistic_plots.create_plot('Colleges')

@ADMIN.route('/admin/graphs/payments')
@login_manager.admin_required
def graph_payments():
    """Render graph showing payment statistics.

    Shows how many tickets have been paid for by each payment method.
    """
    return statistic_plots.create_plot('Payments')

@ADMIN.route('/admin/data/<group>')
@login_manager.admin_required
def data(group):
    """Export statistics as CSV.

    Exports the statistics used to render the graphs as a CSV file.
    """
    stats = models.Statistic.query.filter(
        models.Statistic.group == group.title()
    ).order_by(
        models.Statistic.timestamp
    ).all()

    csvdata = StringIO.StringIO()
    csvwriter = csv.writer(csvdata)

    for stat in stats:
        csvwriter.writerow(
            [
                stat.timestamp.strftime('%c'),
                stat.statistic,
                stat.value
            ]
        )

    csvdata.seek(0)
    return flask.send_file(csvdata, mimetype='text/csv', cache_timeout=900)

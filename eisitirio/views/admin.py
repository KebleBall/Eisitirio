# coding: utf-8
"""Views related to administrative tasks."""

from __future__ import unicode_literals

import csv
import StringIO

from dateutil import parser
from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import login_manager
from eisitirio.helpers import util
from eisitirio.logic import eway_logic

APP = app.APP
DB = db.DB

ADMIN = flask.Blueprint('admin', __name__)

@ADMIN.route('/admin', methods=['GET', 'POST'])
@ADMIN.route('/admin/page/<int:page>', methods=['GET', 'POST'])
@login.login_required
@login_manager.admin_required
def admin_home(page=1):
    """Admin homepage, search for users, tickets or log entries.

    Displays a form with lots of filters on users, tickets and log entries. On
    submission, generates a filtered query for each of users, tickets and log
    entries, and appropriately joins them to return the results of the requested
    type.
    """

    if flask.request.method != 'POST':
        return flask.render_template(
            'admin/admin_home.html',
            form={},
            colleges=models.College.query.all(),
            affiliations=models.Affiliation.query.all(),
            results=None,
            category=None
        )

    user_query = models.User.query
    has_user_filter = False
    ticket_query = models.Ticket.query
    has_ticket_filter = False
    log_query = models.Log.query
    has_log_filter = False

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
            models.Ticket.price_ >= flask.request.form['ticket_min_price']
        )
        has_ticket_filter = True

    if (
            'ticket_max_price' in flask.request.form and
            flask.request.form['ticket_max_price'] != ''
    ):
        ticket_query = ticket_query.filter(
            models.Ticket.price_ <= flask.request.form['ticket_max_price']
        )
        has_ticket_filter = True

    if (
            'ticket_method' in flask.request.form and
            flask.request.form['ticket_method'] != '' and
            flask.request.form['ticket_method'] != 'Any'
    ):
        ticket_query = ticket_query.join(
            models.TicketTransactionItem.query.join(
                models.Transaction.query.filter(
                    models.Transaction.payment_method ==
                    flask.request.form['ticket_method']
                ).filter(
                    models.Transaction.paid == True # pylint: disable=singleton-comparison
                ).subquery(),
                models.TicketTransactionItem.transaction
            ).subquery(reduce_columns=True),
            models.Ticket.transaction_items
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
            'log_ip' in flask.request.form and
            flask.request.form['log_ip'] != ''
    ):
        log_query = log_query.filter(
            models.Log.ip_address == flask.request.form['log_ip']
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

    query = None
    model = None
    category = None

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

        query = user_query
        model = models.User
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
                models.Ticket.events
            )

        query = ticket_query
        model = models.Ticket
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

        query = log_query
        model = models.Log
        category = 'Log'

    if (
            'action' in flask.request.form and
            flask.request.form['action'] == 'Export'
    ):
        csvdata = StringIO.StringIO()
        csvwriter = csv.writer(csvdata)

        model.write_csv_header(csvwriter)

        for result in query.all():
            result.write_csv_row(csvwriter)

        csvdata.seek(0)

        return flask.send_file(csvdata, mimetype='text/csv', cache_timeout=0,
                               attachment_filename="search_results.csv",
                               as_attachment=True)
    else:
        return flask.render_template(
            'admin/admin_home.html',
            form=flask.request.form,
            colleges=models.College.query.all(),
            affiliations=models.Affiliation.query.all(),
            results=query.paginate(page,
                                   int(flask.request.form['num_results'])),
            category=category
        )

@ADMIN.route('/admin/log/<int:entry_id>/view')
@login.login_required
@login_manager.admin_required
def view_log(entry_id):
    """View a log entry."""
    log = models.Log.get_by_id(entry_id)

    return flask.render_template(
        'admin/view_log.html',
        log=log
    )

@ADMIN.route('/admin/transaction/<int:transaction_id>/view')
@ADMIN.route(
    '/admin/transaction/<int:transaction_id>/view/page/<int:events_page>'
)
@login.login_required
@login_manager.admin_required
def view_transaction(transaction_id, events_page=1):
    """View a card transaction object."""
    transaction = models.Transaction.get_by_id(transaction_id)

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

@ADMIN.route('/admin/eway_transaction/<int:eway_transaction_id>/view')
@login.login_required
@login_manager.admin_required
def view_eway_transaction(eway_transaction_id):
    """View a card transaction object."""
    eway_transaction = models.EwayTransaction.get_by_id(eway_transaction_id)

    return flask.render_template(
        'admin/view_eway_transaction.html',
        eway_transaction=eway_transaction,
    )

@ADMIN.route('/admin/eway_transaction/<int:eway_transaction_id>/refund',
             methods=['GET', 'POST'])
@login.login_required
@login_manager.admin_required
def refund_transaction(eway_transaction_id):
    """Refund a transaction.

    Allows part or full refunds for whatever reason, sends a request to eWay to
    refund money back to the user's card.
    """
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

    eway = models.EwayTransaction.get_by_id(eway_transaction_id)

    if eway:
        amount = util.parse_pounds_pence(flask.request.form,
                                         'refund_amount_pounds',
                                         'refund_amount_pence')

        if amount == 0:
            flask.flash(
                'Cannot refund nothing.',
                'warning'
            )
            return flask.redirect(
                flask.request.referrer or
                flask.url_for('admin.view_transaction',
                              transaction_id=eway_transaction_id)
            )

        if amount > (eway.charged - eway.refunded):
            flask.flash(
                'Cannot refund more than has been charged.',
                'warning'
            )
            return flask.redirect(
                flask.request.referrer or
                flask.url_for('admin.view_eway_transaction',
                              eway_transaction_id=eway_transaction_id)
            )

        transaction = models.CardTransaction(eway.transactions[0].user, eway)

        DB.session.add(transaction)

        DB.session.add(models.GenericTransactionItem(
            transaction,
            0 - amount,
            'Manual Refund'
        ))

        DB.session.commit()

        if eway_logic.process_refund(transaction, amount):
            flask.flash(
                'Refund processed successfully.',
                'success'
            )

            transaction.paid = True
            DB.session.commit()

            APP.log_manager.log_event(
                "Manual refund",
                user=transaction.user,
                transaction=transaction
            )
        else:
            flask.flash(
                'Could not process refund.',
                'warning'
            )

        return flask.redirect(
            flask.request.referrer or
            flask.url_for('admin.view_transaction',
                          transaction_id=transaction.transaction_id)
        )
    else:
        flask.flash(
            'Could not find transaction, could not refund.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN.route('/admin/waiting/<int:entry_id>/delete')
@login.login_required
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

@ADMIN.route('/admin/purchase_group/<int:group_id>/view')
@ADMIN.route(
    '/admin/purchase_group/<int:group_id>/view/page/<int:events_page>'
)
@login.login_required
@login_manager.admin_required
def view_purchase_group(group_id, events_page=1):
    """View a ticket object."""
    purchase_group = models.PurchaseGroup.get_by_id(group_id)

    if purchase_group:
        events = purchase_group.events.paginate(
            events_page,
            10,
            True
        )
    else:
        events = None

    return flask.render_template(
        'admin/view_purchase_group.html',
        purchase_group=purchase_group,
        events=events,
        events_page=events_page
    )

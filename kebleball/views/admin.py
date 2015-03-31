# coding: utf-8

import csv
import re
from dateutil.parser import parse
from datetime import datetime

from flask.ext.sqlalchemy import Pagination
from flask.ext.login import current_user, login_user
from flask import Blueprint, render_template, request, flash, send_file, redirect, url_for, session
from StringIO import StringIO
from sqlalchemy import func

from kebleball import app
from kebleball.database import db
from kebleball.database import user
from kebleball.database import college
from kebleball.database import affiliation
from kebleball.database import announcement
from kebleball.database import ticket
from kebleball.database import log
from kebleball.database import statistic
from kebleball.database import waiting
from kebleball.database import card_transaction
from kebleball.database import voucher
from kebleball.helpers import generate_key
from kebleball.helpers.login_manager import admin_required
from kebleball.helpers.statistic_plots import create_plot

APP = app.APP
DB = db.DB

User = user.User
College = college.College
Affiliation = affiliation.Affiliation
Announcement = announcement.Announcement
Ticket = ticket.Ticket
Log = log.Log
Statistic = statistic.Statistic
Waiting = waiting.Waiting
CardTransaction = card_transaction.CardTransaction
Voucher = voucher.Voucher

ADMIN = Blueprint('admin', __name__)

@ADMIN.route('/admin', methods=['GET', 'POST'])
@ADMIN.route('/admin/page/<int:page>', methods=['GET', 'POST'])
@admin_required
def admin_home(page=1):
    results = None
    category = None
    form = {}

    if request.method == 'POST':
        user_query = User.query
        has_user_filter = False
        ticket_query = Ticket.query
        has_ticket_filter = False
        log_query = Log.query
        has_log_filter = False

        num_per_page = int(request.form['numResults'])
        form = request.form

        if (
                'userName' in request.form and
                request.form['userName'] != ''
        ):
            user_query = user_query.filter(
                User.fullname.like('%' + request.form['userName'] + '%'))
            has_user_filter = True

        if (
                'userEmail' in request.form and
                request.form['userEmail'] != ''
        ):
            user_query = user_query.filter(
                User.email == request.form['userEmail'])
            has_user_filter = True

        if (
                'userCollege' in request.form and
                request.form['userCollege'] != '' and
                request.form['userCollege'] != 'Any'
        ):
            user_query = user_query.filter(
                User.college_id == request.form['userCollege'])
            has_user_filter = True

        if (
                'userAffiliation' in request.form and
                request.form['userAffiliation'] != '' and
                request.form['userAffiliation'] != 'Any'
        ):
            user_query = user_query.filter(
                User.affiliation_id == request.form['userAffiliation'])
            has_user_filter = True

        if (
                'userTickets' in request.form and
                request.form['userTickets'] != '' and
                request.form['userTickets'] != 'Any'
        ):
            if request.form['userTickets'] == 'Has':
                user_query = user_query.filter(User.tickets.any())
            else:
                user_query = user_query.filter(~User.tickets.any())
            has_user_filter = True

        if (
                'userWaiting' in request.form and
                request.form['userWaiting'] != '' and
                request.form['userWaiting'] != 'Any'
        ):
            if request.form['userWaiting'] == 'Is':
                user_query = user_query.filter(User.waiting.any())
            else:
                user_query = user_query.filter(~User.waiting.any())
            has_user_filter = True

        if (
                'ticketNumber' in request.form and
                request.form['ticketNumber'] != ''
        ):
            ticket_query = ticket_query.filter(
                Ticket.id == request.form['ticketNumber'])
            has_ticket_filter = True

        if (
                'ticketName' in request.form and
                request.form['ticketName'] != ''
        ):
            ticket_query = ticket_query.filter(
                Ticket.name.like('%' + request.form['ticketName'] + '%'))
            has_ticket_filter = True

        if (
                'ticketBarcode' in request.form and
                request.form['ticketBarcode'] != ''
        ):
            ticket_query = ticket_query.filter(
                Ticket.barcode == request.form['ticketBarcode'])
            has_ticket_filter = True

        if (
                'ticketMinPrice' in request.form and
                request.form['ticketMinPrice'] != ''
        ):
            ticket_query = ticket_query.filter(
                Ticket.price >= request.form['ticketMinPrice'])
            has_ticket_filter = True

        if (
                'ticketMaxPrice' in request.form and
                request.form['ticketMaxPrice'] != ''
        ):
            ticket_query = ticket_query.filter(
                Ticket.price <= request.form['ticketMaxPrice'])
            has_ticket_filter = True

        if (
                'ticketMethod' in request.form and
                request.form['ticketMethod'] != '' and
                request.form['ticketMethod'] != 'Any'
        ):
            ticket_query = ticket_query.filter(
                Ticket.paymentmethod == request.form['ticketMethod'])
            has_ticket_filter = True

        if (
                'ticketPaid' in request.form and
                request.form['ticketPaid'] != '' and
                request.form['ticketPaid'] != 'Any'
        ):
            ticket_query = ticket_query.filter(
                Ticket.paid == (request.form['ticketPaid'] == 'Is'))
            has_ticket_filter = True

        if (
                'ticketCollected' in request.form and
                request.form['ticketCollected'] != '' and
                request.form['ticketCollected'] != 'Any'
        ):
            ticket_query = ticket_query.filter(
                Ticket.collected == (request.form['ticketCollected'] == 'Is'))
            has_ticket_filter = True

        if (
                'ticketReferrer' in request.form and
                request.form['ticketReferrer'] != '' and
                request.form['ticketReferrer'] != 'Any'
        ):
            if request.form['ticketReferrer'] == 'Has':
                ticket_query = ticket_query.filter(Ticket.referrer_id != None)
            else:
                ticket_query = ticket_query.filter(Ticket.referrer_id == None)
            has_ticket_filter = True

        if (
                'logIP' in request.form and
                request.form['logIP'] != ''
        ):
            log_query = log_query.filter(Log.ip == request.form['logIP'])
            has_log_filter = True

        if (
                'logStart' in request.form and
                request.form['logStart'] != ''
        ):
            try:
                dtstamp = parse(request.form['logStart'])
                log_query = log_query.filter(Log.timestamp >= dtstamp)
                has_log_filter = True
            except ValueError, TypeError:
                flash(
                    'Could not parse start date/time, ignoring.',
                    'warning'
                )

        if (
                'logEnd' in request.form and
                request.form['logEnd'] != ''
        ):
            try:
                dtstamp = parse(request.form['logEnd'])
                log_query = log_query.filter(Log.timestamp <= dtstamp)
                has_log_filter = True
            except ValueError, TypeError:
                flash(
                    'Could not parse end date/time, ignoring.',
                    'warning'
                )

        if (
                'logMessage' in request.form and
                request.form['logMessage'] != ''
        ):
            log_query = log_query.filter(
                Log.action.like('%' + request.form['logMessage'] + '%'))
            has_log_filter = True

        log_query = log_query.order_by(Log.timestamp.desc())

        if request.form['search'] == 'user':
            if has_ticket_filter:
                user_query = user_query.join(
                    ticket_query.subquery(),
                    User.tickets
                )

            if has_log_filter:
                if request.form['logUser'] == 'Actor':
                    user_query = user_query.join(
                        log_query.subquery(),
                        User.actions
                    )
                else:
                    user_query = user_query.join(
                        log_query.subquery(),
                        User.events
                    )

            results = user_query.paginate(page, num_per_page)
            category = 'User'
        elif request.form['search'] == 'ticket':
            if has_user_filter:
                ticket_query = ticket_query.join(
                    user_query.subquery(),
                    Ticket.owner
                )

            if has_log_filter:
                ticket_query = ticket_query.join(
                    log_query.subquery(),
                    Ticket.log_entries
                )

            results = ticket_query.paginate(page, num_per_page)
            category = 'Ticket'
        elif request.form['search'] == 'log':
            if has_user_filter:
                if request.form['logUser'] == 'Actor':
                    log_query = log_query.join(
                        user_query.subquery(),
                        Log.actor
                    )
                else:
                    log_query = log_query.join(
                        user_query.subquery(),
                        Log.user
                    )

            if has_ticket_filter:
                log_query = log_query.join(
                    ticket_query.subquery(),
                    Log.tickets
                )

            results = log_query.paginate(page, num_per_page)
            category = 'Log'

    return render_template(
        'admin/admin_home.html',
        form=form,
        colleges=College.query.all(),
        affiliations=Affiliation.query.all(),
        results=results,
        category=category
    )

@ADMIN.route('/admin/user/<int:id>/view')
@ADMIN.route('/admin/user/<int:id>/view/page/selfactions/<int:self_actions_page>')
@ADMIN.route('/admin/user/<int:id>/view/page/actions/<int:actions_page>')
@ADMIN.route('/admin/user/<int:id>/view/page/events/<int:events_page>')
@admin_required
def view_user(id, self_actions_page=1, actions_page=1, events_page=1):
    user = User.get_by_id(id)

    if user:
        self_actions = user.actions \
            .filter(Log.actor_id == Log.user_id) \
            .order_by(Log.timestamp.desc()) \
            .paginate(
                self_actions_page,
                10,
                True
            )
        other_actions = user.actions \
            .filter(Log.actor_id != Log.user_id) \
            .order_by(Log.timestamp.desc()) \
            .paginate(
                actions_page,
                10,
                True
            )
        events = user.events \
            .filter(Log.actor_id != Log.user_id) \
            .order_by(Log.timestamp.desc()) \
            .paginate(
                events_page,
                10,
                True
            )
    else:
        self_actions = None
        other_actions = None
        events = None

    return render_template(
        'admin/view_user.html',
        user=user,
        self_actions=self_actions,
        other_actions=other_actions,
        events=events,
        self_actions_page=self_actions_page,
        actions_page=actions_page,
        events_page=events_page
    )

@ADMIN.route('/admin/user/<int:id>/impersonate')
@admin_required
def impersonate_user(id):
    user = User.get_by_id(id)

    if user:
        session['actor_id'] = current_user.id

        login_user(
            user,
            remember=False
        )

        APP.log_manager.log_event(
            'Started impersonating user',
            [],
            user
        )

        return redirect(url_for('dashboard.dashboard_home'))
    else:
        flash(
            u'Could not find user, could not impersonate.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.admin_home'))

@ADMIN.route('/admin/user/<int:id>/give', methods=['GET', 'POST'])
@admin_required
def give_user(id):
    if request.method != 'POST':
        return redirect(request.referrer or url_for('admin.adminHome'))

    user = User.get_by_id(id)

    if user:
        price = (
            int(request.form['givePricePounds']) * 100 +
            int(request.form['givePricePence'])
        )
        num_tickets = int(request.form['giveNumTickets'])

        if (
                'giveReason' not in request.form or
                request.form['giveReason'] == ''
        ):
            note = 'Given by {0} (#{1}) for no reason.'.format(
                current_user.fullname,
                current_user.id
            )
        else:
            note = 'Given by {0} (#{1}) with reason: {2}.'.format(
                current_user.fullname,
                current_user.id,
                request.form['giveReason']
            )

        tickets = []

        for _ in xrange(num_tickets):
            ticket = Ticket(
                user,
                None,
                price
            )
            ticket.add_note(note)
            tickets.append(ticket)

        DB.session.add_all(tickets)
        DB.session.commit()

        APP.log_manager.log_event(
            'Gave {0} tickets'.format(
                num_tickets
            ),
            tickets,
            user
        )

        flash(
            u'Gave {0} {1} tickets'.format(
                user.firstname,
                num_tickets
            ),
            'success'
        )

        return redirect(request.referrer
                        or url_for('admin.view_user', id=user.id))
    else:
        flash(
            u'Could not find user, could not give tickets.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.admin_home'))

@ADMIN.route('/admin/user/<int:id>/note', methods=['GET', 'POST'])
@admin_required
def note_user(id):
    if request.method != 'POST':
        return redirect(request.referrer or url_for('admin.adminHome'))

    user = User.get_by_id(id)

    if user:
        user.note = request.form['notes']
        DB.session.commit()

        APP.log_manager.log_event(
            'Updated notes',
            [],
            user
        )

        flash(
            u'Notes set successfully.',
            'success'
        )
        return redirect(request.referrer
                        or url_for('admin.view_user', id=user.id))
    else:
        flash(
            u'Could not find user, could not set notes.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.admin_home'))

@ADMIN.route('/admin/user/<int:id>/verify')
@admin_required
def verify_user(id):
    user = User.get_by_id(id)

    if user:
        user.verified = True
        DB.session.commit()

        APP.log_manager.log_event(
            'Verified email',
            [],
            user
        )

        flash(
            u'User marked as verified.',
            'success'
        )
        return redirect(request.referrer
                        or url_for('admin.view_user', id=user.id))
    else:
        flash(
            u'Could not find user, could not verify.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.admin_home'))

@ADMIN.route('/admin/user/<int:id>/demote')
@admin_required
def demote_user(id):
    user = User.get_by_id(id)

    if user:
        user.demote()
        DB.session.commit()

        APP.log_manager.log_event(
            'Demoted user',
            [],
            user
        )

        flash(
            u'User demoted.',
            'success'
        )
        return redirect(request.referrer
                        or url_for('admin.view_user', id=user.id))
    else:
        flash(
            u'Could not find user, could not demote.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.admin_home'))

@ADMIN.route('/admin/user/<int:id>/promote')
@admin_required
def promote_user(id):
    user = User.get_by_id(id)

    if user:
        user.promote()
        DB.session.commit()

        APP.log_manager.log_event(
            'Promoted user',
            [],
            user
        )

        flash(
            u'User promoted.',
            'success'
        )
        return redirect(request.referrer
                        or url_for('admin.view_user', id=user.id))
    else:
        flash(
            u'Could not find user, could not promote.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.admin_home'))

@ADMIN.route('/admin/user/<int:id>/add_manual_battels')
@admin_required
def add_manual_battels(id):
    user = User.get_by_id(id)

    if user:
        user.add_manual_battels()

        APP.log_manager.log_event(
            'Manually set up battels',
            [],
            user
        )

        flash(
            u'Battels set up for user.',
            'success'
        )
        return redirect(request.referrer or url_for('admin.viewUser', id=user.id))
    else:
        flash(
            u'Could not find user, could not manually set up battels.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.adminHome'))

@ADMIN.route('/admin/user/<int:id>/verify_affiliation')
@admin_required
def verify_affiliation(id):
    user = User.get_by_id(id)

    if user:
        user.verify_affiliation()

        APP.log_manager.log_event(
            'Verified affiliation',
            [],
            user
        )

    return redirect(url_for('admin.verify_affiliations'))

@ADMIN.route('/admin/user/<int:id>/deny_affiliation')
@admin_required
def deny_affiliation(id):
    user = User.get_by_id(id)

    if user:
        user.deny_affiliation()

        APP.log_manager.log_event(
            'Denied affiliation',
            [],
            user
        )

    return redirect(url_for('admin.verify_affiliations'))

@ADMIN.route("/admin/verify_affiliations")
@admin_required
def verify_affiliations():
    users = User.query.filter(
        User.college.has(name="Keble")
    ).filter(
        User.affiliation_verified == None
    ).all()

    return render_template('admin/verify_affiliations.html', users=users)

@ADMIN.route('/admin/user/<int:id>/collect', methods=['GET', 'POST'])
@admin_required
def collect_tickets(id):
    user = User.get_by_id(id)

    if user:
        return render_template(
            'admin/collect_tickets.html',
            user=user
        )
    else:
        flash(
            u'Could not find user, could not process ticket collection.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.admin_home'))

@ADMIN.route('/admin/ticket/<int:id>/view')
@ADMIN.route('/admin/ticket/<int:id>/view/page/<int:events_page>')
@admin_required
def view_ticket(id, events_page=1):
    ticket = Ticket.get_by_id(id)

    if ticket:
        events = ticket.log_entries \
            .paginate(
                events_page,
                10,
                True
            )
    else:
        events = None

    return render_template(
        'admin/view_ticket.html',
        ticket=ticket,
        events=events,
        events_page=events_page
    )

@ADMIN.route('/admin/ticket/<int:id>/collect', methods=['GET', 'POST'])
@admin_required
def collect_ticket(id):
    if request.method != 'POST':
        return redirect(request.referrer or url_for('admin.adminHome'))

    existing = Ticket.query.filter(
        Ticket.barcode == request.form['barcode']
    ).count()

    if existing > 0:
        flash(
            u'Barcode has already been used for a ticket.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.admin_home'))

    ticket = Ticket.get_by_id(id)

    if ticket:
        ticket.barcode = request.form['barcode']
        ticket.collected = True
        DB.session.commit()

        APP.log_manager.log_event(
            'Collected',
            [ticket]
        )

        flash(
            u'Ticket marked as collected with barcode number {0}.'.format(
                request.form['barcode']
            ),
            'success'
        )
        return redirect(request.referrer
                        or url_for('admin.collect_tickets', id=ticket.owner_id))
    else:
        flash(
            u'Could not find ticket, could mark as collected.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.admin_home'))

@ADMIN.route('/admin/ticket/<int:id>/note', methods=['GET', 'POST'])
@admin_required
def note_ticket(id):
    if request.method != 'POST':
        return redirect(request.referrer or url_for('admin.adminHome'))

    ticket = Ticket.get_by_id(id)

    if ticket:
        ticket.note = request.form['notes']
        DB.session.commit()

        APP.log_manager.log_event(
            'Updated notes',
            [ticket]
        )

        flash(
            u'Notes set successfully.',
            'success'
        )
        return redirect(request.referrer
                        or url_for('admin.view_ticket', id=ticket.id))
    else:
        flash(
            u'Could not find ticket, could not set notes.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.admin_home'))

@ADMIN.route('/admin/ticket/<int:id>/markpaid')
@admin_required
def mark_ticket_paid(id):
    ticket = Ticket.get_by_id(id)

    if ticket:
        ticket.paid = True
        DB.session.commit()

        APP.log_manager.log_event(
            'Marked as paid',
            [ticket]
        )

        flash(
            u'Ticket successfully marked as paid.',
            'success'
        )
        return redirect(request.referrer
                        or url_for('admin.view_ticket', id=ticket.id))
    else:
        flash(
            u'Could not find ticket, could not mark as paid.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.admin_home'))

@ADMIN.route('/admin/ticket/<int:id>/autocancel')
@admin_required
def auto_cancel_ticket(id):
    ticket = Ticket.get_by_id(id)

    if ticket:
        if not ticket.can_be_cancelled_automatically():
            flash(
                u'Could not automatically cancel ticket.',
                'warning'
            )
            return redirect(request.referrer
                            or url_for('admin.view_ticket', id=ticket.id))

        if ticket.paymentmethod == 'Battels':
            ticket.battels.cancel(ticket)
        elif ticket.paymentmethod == 'Card':
            refund_result = ticket.card_transaction.process_refund(ticket.price)
            if not refund_result:
                flash(
                    u'Could not process card refund.',
                    'warning'
                )
                return redirect(request.referrer
                                or url_for('admin.view_ticket', id=ticket.id))

        ticket.cancelled = True
        DB.session.commit()

        APP.log_manager.log_event(
            'Cancelled and refunded ticket',
            [ticket]
        )

        flash(
            u'Ticket cancelled successfully.',
            'success'
        )
        return redirect(request.referrer
                        or url_for('admin.view_ticket', id=ticket.id))
    else:
        flash(
            u'Could not find ticket, could not cancel.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.admin_home'))

@ADMIN.route('/admin/ticket/<int:id>/cancel')
@admin_required
def cancel_ticket(id):
    ticket = Ticket.get_by_id(id)

    if ticket:
        ticket.cancelled = True
        DB.session.commit()

        APP.log_manager.log_event(
            'Marked ticket as cancelled',
            [ticket]
        )

        flash(
            u'Ticket cancelled successfully.',
            'success'
        )
        return redirect(request.referrer
                        or url_for('admin.view_ticket', id=ticket.id))
    else:
        flash(
            u'Could not find ticket, could not cancel.',
            'warning'
        )
        return redirect(request.referrer
                        or url_for('admin.admin_home'))

@ADMIN.route('/admin/ticket/validate', methods=['POST', 'GET'])
@admin_required
def validate_ticket():
    valid = None
    message = None

    if request.method == 'POST':
        ticket = Ticket.query.filter(
            Ticket.barcode == request.form['barcode']).first()

        if not ticket:
            valid = False
            message = "No such ticket with barcode {0}".format(
                request.form['barcode'])
        elif ticket.entered:
            valid = False
            message = (
                "Ticket has already been used for "
                "entry. Check ID against {0} (owned by {1})"
            ).format(
                ticket.name,
                ticket.owner.fullname
            )
        else:
            ticket.entered = True
            DB.session.commit()
            valid = True
            message = "Permit entry for {0}".format(ticket.name)

    return render_template(
        'admin/validate_ticket.html',
        valid=valid,
        message=message
    )

@ADMIN.route('/admin/log/<int:id>/view')
@admin_required
def view_log(id):
    log = Log.get_by_id(id)

    return render_template(
        'admin/view_log.html',
        log=log
    )

@ADMIN.route('/admin/transaction/<int:id>/view')
@ADMIN.route('/admin/transaction/<int:id>/view/page/<int:events_page>')
@admin_required
def view_transaction(id, events_page=1):
    transaction = CardTransaction.get_by_id(id)

    if transaction:
        events = transaction.events \
            .paginate(
                events_page,
                10,
                True
            )
    else:
        events = None

    return render_template(
        'admin/view_transaction.html',
        transaction=transaction,
        events=events,
        events_page=events_page
    )

@ADMIN.route('/admin/transaction/<int:id>/refund', methods=['GET', 'POST'])
@admin_required
def refund_transaction(id):
    if request.method != 'POST':
        return redirect(request.referrer or url_for('admin.adminHome'))

    transaction = CardTransaction.get_by_id(id)

    if transaction:
        amount = (int(request.form['refundAmountPounds'])
                  * 100 + int(request.form['refundAmountPence']))

        if amount > (transaction.get_value() - transaction.refunded):
            flash(
                u'Cannot refund more than has been charged.',
                'warning'
            )
            return redirect(request.referrer
                            or url_for('admin.view_transaction', id=transaction.id))

        result = transaction.process_refund(amount)

        if not result:
            flash(
                u'Could not process refund.',
                'warning'
            )
        else:
            flash(
                u'Refund processed successfully.',
                'success'
            )
        return redirect(request.referrer
                        or url_for('admin.view_transaction', id=transaction.id))
    else:
        flash(
            u'Could not find transaction, could not cancel.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.admin_home'))

@ADMIN.route('/admin/statistics')
@admin_required
def statistics():
    total_value = DB.session \
        .query(func.sum(Ticket.price)) \
        .filter(Ticket.cancelled != True) \
        .scalar()

    if total_value is None:
        total_value = 0

    paid_value = DB.session \
        .query(func.sum(Ticket.price)) \
        .filter(Ticket.paid == True) \
        .filter(Ticket.cancelled != True) \
        .scalar()

    if paid_value is None:
        paid_value = 0

    cancelled_value = DB.session \
        .query(func.sum(Ticket.price)) \
        .filter(Ticket.cancelled == True) \
        .scalar()

    if cancelled_value is None:
        cancelled_value = 0

    payment_method_values = DB.session \
        .query(func.sum(Ticket.price), Ticket.paymentmethod) \
        .filter(Ticket.cancelled != True) \
        .group_by(Ticket.paymentmethod) \
        .all()

    return render_template(
        'admin/statistics.html',
        total_value=total_value,
        paid_value=paid_value,
        cancelled_value=cancelled_value,
        payment_method_values=payment_method_values
    )

@ADMIN.route('/admin/announcements', methods=['GET', 'POST'])
@ADMIN.route('/admin/announcements/page/<int:page>', methods=['GET', 'POST'])
@admin_required
def announcements(page=1):
    form = {}

    if request.method == 'POST':
        form = request.form

        success = True

        if 'subject' not in form or form['subject'] == '':
            flash(
                u'Subject must not be blank',
                'warning'
            )
            success = False

        if 'message' not in form or form['message'] == '':
            flash(
                u'Message must not be blank',
                'warning'
            )
            success = False

        if 'tickets' in form and form['tickets'] == 'no':
            if 'collected' in form and form['collected'] == 'yes':
                flash(
                    u'A person cannot have no tickets and have collected tickets',
                    'warning'
                )
                success = False
            if 'uncollected' in form and form['uncollected'] == 'yes':
                flash(
                    u'A person cannot have no tickets and have uncollected tickets',
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

            announcement = Announcement(
                form['subject'],
                form['message'],
                current_user,
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

            flash(
                u'Announcement created successfully',
                'success'
            )

            form = {}

    return render_template(
        'admin/announcements.html',
        colleges=College.query.all(),
        affiliations=Affiliation.query.all(),
        announcements=Announcement.query.paginate(page, 10, False),
        form=form
    )

@ADMIN.route('/admin/announcement/<int:id>/delete')
@admin_required
def deleteAnnouncement(id):
    announcement = Announcement.get_by_id(id)

    if announcement:
        DB.session.delete(announcement)
        DB.session.commit()

        flash(
            u'Announcement deleted successfully',
            'success'
        )
    else:
        flash(
            u'Could not find announcement, could not delete',
            'warning'
        )

    return redirect(request.referrer or url_for('admin.announcements'))

@ADMIN.route('/admin/announcement/<int:id>/cancel')
@admin_required
def cancelAnnouncementEmails(id):
    announcement = Announcement.get_by_id(id)

    if announcement:
        announcement.emails = []
        announcement.send_email = False
        DB.session.commit()

        flash(
            u'Announcement emails cancelled successfully',
            'success'
        )
    else:
        flash(
            u'Could not find announcement, could not cancel emails',
            'warning'
        )

    return redirect(request.referrer or url_for('admin.announcements'))

@ADMIN.route('/admin/vouchers', methods=['GET', 'POST'])
@ADMIN.route('/admin/vouchers/page/<int:page>', methods=['GET', 'POST'])
@admin_required
def vouchers(page=1):
    form = {}

    if request.method == 'POST':
        form = request.form

        success = True

        expires = None

        if 'expires' in form and form['expires'] != '':
            try:
                expires = parse(form['expires'])
                if expires < datetime.utcnow():
                    flash(
                        u'Expiry date cannot be in the past',
                        'warning'
                    )
                    success = False
            except KeyError, ValueError:
                flash(
                    u'Could not parse expiry date',
                    'warning'
                )
                success = False

        if 'voucherType' not in form or form['voucherType'] == '':
            flash(
                u'You must select a discout type',
                'warning'
            )
            success = False
        elif form['voucherType'] == 'Fixed Price':
            value = (int(form['fixedPricePounds'])
                     * 100 + int(form['fixedPricePence']))
        elif form['voucherType'] == 'Fixed Discount':
            value = (int(form['fixedDiscountPounds'])
                     * 100 + int(form['fixedDiscountPence']))
        else:
            value = int(form['fixedDiscount'])
            if value > 100:
                flash(
                    u'Cannot give greater than 100% discount',
                    'warning'
                )
                success = False

        if not re.match('[a-zA-Z0-9]+', form['voucherPrefix']):
            flash(
                u'Voucher prefix must be non-empty and contain only letters and numbers',
                'warning'
            )
            success = False

        if success:
            num_vouchers = int(form['num_vouchers'])
            single_use = 'single_use' in form and form['single_use'] == 'yes'

            for _ in xrange(num_vouchers):
                key = generate_key(10)
                voucher = Voucher(
                    '{0}-{1}'.format(
                        form['voucherPrefix'],
                        key
                    ),
                    expires,
                    form['voucherType'],
                    value,
                    form['appliesTo'],
                    single_use
                )
                DB.session.add(voucher)

            DB.session.commit()

            flash(
                u'Voucher(s) created successfully',
                'success'
            )

            form = {}

    vouchers = Voucher.query

    if 'search' in request.args:
        vouchers = vouchers.filter(
            Voucher.code.like(
                '%{0}%'.format(
                    request.args['search']
                )
            )
        )

    vouchers = vouchers.paginate(
        page,
        10
    )

    return render_template(
        'admin/vouchers.html',
        form=form,
        vouchers=vouchers
    )

@ADMIN.route('/admin/voucher/<int:id>/delete')
@admin_required
def deleteVoucher(id):
    voucher = Voucher.get_by_id(id)

    if voucher:
        DB.session.delete(voucher)
        DB.session.commit()
        flash(
            u'Voucher deleted successfully',
            'success'
        )
    else:
        flash(
            u'Could not find voucher to delete',
            'warning'
        )

    return redirect(request.referrer or url_for('admin.vouchers'))

@ADMIN.route('/admin/waiting/<int:id>/delete')
@admin_required
def deleteWaiting(id):
    waiting = Waiting.get_by_id(id)

    if waiting:
        DB.session.delete(waiting)
        DB.session.commit()
        flash(
            u'Waiting list entry deleted',
            'success'
        )
    else:
        flash(
            u'Waiting list entry not found, could not delete.',
            'error'
        )

    return redirect(request.referrer or url_for('admin.admin_home'))

@ADMIN.route('/admin/graphs/sales')
@admin_required
def graphSales():
    statistics = Statistic.query \
        .filter(Statistic.group == 'Sales') \
        .order_by(Statistic.timestamp) \
        .all()

    statistic_keys = [
        ('Available', 'g-'),
        ('Ordered', 'b-'),
        ('Paid', 'r-'),
        ('Cancelled', 'y-'),
        ('Collected', 'c-'),
        ('Waiting', 'm-')
    ]

    plots = {
        key: {
            'timestamps': [],
            'datapoints': [],
            'line': line,
            'currentValue': 0
        } for (key, line) in statistic_keys
    }

    for statistic in statistics:
        plots[statistic.statistic]['timestamps'].append(statistic.timestamp)
        plots[statistic.statistic]['datapoints'].append(statistic.value)
        plots[statistic.statistic]['currentValue'] = statistic.value

    return create_plot(plots, statistics[0].timestamp, statistics[-1].timestamp)

@ADMIN.route('/admin/graphs/colleges')
@admin_required
def graphColleges():
    statistics = Statistic.query \
        .filter(Statistic.group == 'Colleges') \
        .order_by(Statistic.timestamp) \
        .all()

    statistic_keys = [
        ("All Souls", "r^-"),
        ("Balliol", "g^-"),
        ("Blackfriars", "b^-"),
        ("Brasenose", "c^-"),
        ("Campion Hall", "m^-"),
        ("Christ Church", "y^-"),
        ("Corpus Christi", "ro-"),
        ("Exeter", "go-"),
        ("Green Templeton", "bo-"),
        ("Harris Manchester", "co-"),
        ("Hertford", "mo-"),
        ("Jesus", "yo-"),
        ("Keble", "rs-"),
        ("Kellogg", "gs-"),
        ("Lady Margaret Hall", "bs-"),
        ("Linacre", "cs-"),
        ("Lincoln", "ms-"),
        ("Magdelen", "ys-"),
        ("Mansfield", "r*-"),
        ("Merton", "g*-"),
        ("New", "b*-"),
        ("Nuffield", "c*-"),
        ("Oriel", "m*-"),
        ("Pembroke", "y*-"),
        ("Queen's", "r+-"),
        ("Regent's Park", "g+-"),
        ("Somerville", "b+-"),
        ("St Anne's", "c+-"),
        ("St Antony's", "m+-"),
        ("St Benet's Hall", "y+-"),
        ("St Catherine's", "rx-"),
        ("St Cross", "gx-"),
        ("St Edmund Hall", "bx-"),
        ("St Hilda's", "cx-"),
        ("St Hugh's", "mx-"),
        ("St John's", "yx-"),
        ("St Peter's", "rD-"),
        ("St Stephen's House", "gD-"),
        ("Trinity", "bD-"),
        ("University", "cD-"),
        ("Wadham", "mD-"),
        ("Wolfson", "yD-"),
        ("Worcester", "rH-"),
        ("Wycliffe Hall", "gH-"),
        ("Other", "bH-"),
        ("None", "cH-")
    ]

    plots = {
        key: {
            'timestamps': [],
            'datapoints': [],
            'line': line,
            'currentValue': 0
        } for (key, line) in statistic_keys
    }

    for statistic in statistics:
        plots[statistic.statistic]['timestamps'].append(statistic.timestamp)
        plots[statistic.statistic]['datapoints'].append(statistic.value)
        plots[statistic.statistic]['currentValue'] = statistic.value

    return create_plot(plots, statistics[0].timestamp, statistics[-1].timestamp)

@ADMIN.route('/admin/graphs/payments')
@admin_required
def graphPayments():
    statistics = Statistic.query \
        .filter(Statistic.group == 'Payments') \
        .order_by(Statistic.timestamp) \
        .all()

    statistic_keys = [
        ('Battels', 'g-'),
        ('Card', 'b-'),
        ('Cash', 'r-'),
        ('Cheque', 'y-'),
        ('Free', 'c-')
    ]

    plots = {
        key: {
            'timestamps': [],
            'datapoints': [],
            'line': line,
            'currentValue': 0
        } for (key, line) in statistic_keys
    }

    for statistic in statistics:
        plots[statistic.statistic]['timestamps'].append(statistic.timestamp)
        plots[statistic.statistic]['datapoints'].append(statistic.value)
        plots[statistic.statistic]['currentValue'] = statistic.value

    return create_plot(plots, statistics[0].timestamp, statistics[-1].timestamp)

@ADMIN.route('/admin/data/<group>')
@admin_required
def data(group):
    statistics = Statistic.query \
        .filter(Statistic.group == group.title()) \
        .order_by(Statistic.timestamp) \
        .all()

    csvdata = StringIO()
    csvwriter = csv.writer(csvdata)

    for stat in statistics:
        csvwriter.writerow(
            [
                stat.timestamp.strftime('%c'),
                stat.statistic,
                stat.value
            ]
        )

    csvdata.seek(0)
    return send_file(csvdata, mimetype="text/csv", cache_timeout=900)

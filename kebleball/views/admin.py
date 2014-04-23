# coding: utf-8
from flask import Blueprint, render_template, request, flash, send_file, redirect, url_for, session

from kebleball.app import app
from kebleball.helpers.login_manager import admin_required
from kebleball.database import db
from kebleball.database.user import User
from kebleball.database.college import College
from kebleball.database.affiliation import Affiliation
from kebleball.database.announcement import Announcement
from kebleball.database.ticket import Ticket
from kebleball.database.log import Log
from kebleball.database.statistic import Statistic
from kebleball.database.waiting import Waiting
from kebleball.database.card_transaction import CardTransaction
from kebleball.database.voucher import Voucher
from flask.ext.sqlalchemy import Pagination
from flask.ext.login import current_user, login_user
from dateutil.parser import parse
from datetime import datetime
from kebleball.helpers.statistic_plots import create_plot
from kebleball.helpers import generate_key
from StringIO import StringIO
from sqlalchemy import func
import csv
import re

log = app.log_manager.log_admin
log_event = app.log_manager.log_event

admin = Blueprint('admin', __name__)

@admin.route('/admin', methods=['GET', 'POST'])
@admin.route('/admin/page/<int:page>', methods=['GET', 'POST'])
@admin_required
def adminHome(page=1):
    results = None
    category = None
    form = {}

    if request.method == 'POST':
        userQuery = User.query
        hasUserFilter = False
        ticketQuery = Ticket.query
        hasTicketFilter = False
        logQuery = Log.query
        hasLogFilter = False

        numPerPage = int(request.form['numResults'])
        form = request.form

        if (
            'userName' in request.form and
            request.form['userName'] != ''
        ):
            userQuery = userQuery.filter(User.fullname.like('%' + request.form['userName'] + '%'))
            hasUserFilter = True

        if (
            'userEmail' in request.form and
            request.form['userEmail'] != ''
        ):
            userQuery = userQuery.filter(User.email == request.form['userEmail'])
            hasUserFilter = True

        if (
            'userCollege' in request.form and
            request.form['userCollege'] != '' and
            request.form['userCollege'] != 'Any'
        ):
            userQuery = userQuery.filter(User.college_id == request.form['userCollege'])
            hasUserFilter = True

        if (
            'userAffiliation' in request.form and
            request.form['userAffiliation'] != '' and
            request.form['userAffiliation'] != 'Any'
        ):
            userQuery = userQuery.filter(User.affiliation_id == request.form['userAffiliation'])
            hasUserFilter = True

        if (
            'userTickets' in request.form and
            request.form['userTickets'] != '' and
            request.form['userTickets'] != 'Any'
        ):
            if request.form['userTickets'] == 'Has':
                userQuery = userQuery.filter(User.tickets.any())
            else:
                userQuery = userQuery.filter(~User.tickets.any())
            hasUserFilter = True

        if (
            'userWaiting' in request.form and
            request.form['userWaiting'] != '' and
            request.form['userWaiting'] != 'Any'
        ):
            if request.form['userWaiting'] == 'Is':
                userQuery = userQuery.filter(User.waiting.any())
            else:
                userQuery = userQuery.filter(~User.waiting.any())
            hasUserFilter = True

        if (
            'ticketNumber' in request.form and
            request.form['ticketNumber'] != ''
        ):
            ticketQuery = ticketQuery.filter(Ticket.id == request.form['ticketNumber'])
            hasTicketFilter = True

        if (
            'ticketName' in request.form and
            request.form['ticketName'] != ''
        ):
            ticketQuery = ticketQuery.filter(Ticket.name.like('%' + request.form['ticketName'] + '%'))
            hasTicketFilter = True

        if (
            'ticketMinPrice' in request.form and
            request.form['ticketMinPrice'] != ''
        ):
            ticketQuery = ticketQuery.filter(Ticket.price >= request.form['ticketMinPrice'])
            hasTicketFilter = True

        if (
            'ticketMaxPrice' in request.form and
            request.form['ticketMaxPrice'] != ''
        ):
            ticketQuery = ticketQuery.filter(Ticket.price <= request.form['ticketMaxPrice'])
            hasTicketFilter = True

        if (
            'ticketMethod' in request.form and
            request.form['ticketMethod'] != '' and
            request.form['ticketMethod'] != 'Any'
        ):
            ticketQuery = ticketQuery.filter(Ticket.paymentmethod == request.form['ticketMethod'])
            hasTicketFilter = True

        if (
            'ticketPaid' in request.form and
            request.form['ticketPaid'] != '' and
            request.form['ticketPaid'] != 'Any'
        ):
            ticketQuery = ticketQuery.filter(Ticket.paid == (request.form['ticketPaid'] == 'Is'))
            hasTicketFilter = True

        if (
            'ticketCollected' in request.form and
            request.form['ticketCollected'] != '' and
            request.form['ticketCollected'] != 'Any'
        ):
            ticketQuery = ticketQuery.filter(Ticket.collected == (request.form['ticketCollected'] == 'Is'))
            hasTicketFilter = True

        if (
            'ticketReferrer' in request.form and
            request.form['ticketReferrer'] != '' and
            request.form['ticketReferrer'] != 'Any'
        ):
            if request.form['ticketReferrer'] == 'Has':
                ticketQuery = ticketQuery.filter(Ticket.referrer_id != None)
            else:
                ticketQuery = ticketQuery.filter(Ticket.referrer_id == None)
            hasTicketFilter = True

        if (
            'logIP' in request.form and
            request.form['logIP'] != ''
        ):
            logQuery = logQuery.filter(Log.ip == request.form['logIP'])
            hasLogFilter = True

        if (
            'logStart' in request.form and
            request.form['logStart'] != ''
        ):
            try:
                dt = parse(request.form['logStart'])
                logQuery = logQuery.filter(Log.timestamp >= dt)
                hasLogFilter = True
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
                dt = parse(request.form['logEnd'])
                logQuery = logQuery.filter(Log.timestamp <= dt)
                hasLogFilter = True
            except ValueError, TypeError:
                flash(
                    'Could not parse end date/time, ignoring.',
                    'warning'
                )

        if (
            'logMessage' in request.form and
            request.form['logMessage'] != ''
        ):
            logQuery = logQuery.filter(Log.action.like('%' + request.form['logMessage'] + '%'))
            hasLogFilter = True

        logQuery = logQuery.order_by(Log.timestamp.desc())

        if request.form['search'] == 'user':
            if hasTicketFilter:
                userQuery = userQuery.join(
                    ticketQuery.subquery(),
                    User.tickets
                )

            if hasLogFilter:
                if request.form['logUser'] == 'Actor':
                    userQuery = userQuery.join(
                        logQuery.subquery(),
                        User.actions
                    )
                else:
                    userQuery = userQuery.join(
                        logQuery.subquery(),
                        User.events
                    )

            results = userQuery.paginate(page, numPerPage)
            category = 'User'
        elif request.form['search'] == 'ticket':
            if hasUserFilter:
                ticketQuery = ticketQuery.join(
                    userQuery.subquery(),
                    Ticket.owner
                )

            if hasLogFilter:
                ticketQuery = ticketQuery.join(
                    logQuery.subquery(),
                    Ticket.log_entries
                )

            results = ticketQuery.paginate(page, numPerPage)
            category = 'Ticket'
        elif request.form['search'] == 'log':
            if hasUserFilter:
                if request.form['logUser'] == 'Actor':
                    logQuery = logQuery.join(
                        userQuery.subquery(),
                        Log.actor
                    )
                else:
                    logQuery = logQuery.join(
                        userQuery.subquery(),
                        Log.user
                    )

            if hasTicketFilter:
                logQuery = logQuery.join(
                    ticketQuery.subquery(),
                    Log.tickets
                )

            results = logQuery.paginate(page, numPerPage)
            category = 'Log'

    return render_template(
        'admin/adminHome.html',
        form=form,
        colleges = College.query.all(),
        affiliations = Affiliation.query.all(),
        results=results,
        category=category
    )

@admin.route('/admin/user/<int:id>/view')
@admin.route('/admin/user/<int:id>/view/page/selfactions/<int:selfActionsPage>')
@admin.route('/admin/user/<int:id>/view/page/actions/<int:actionsPage>')
@admin.route('/admin/user/<int:id>/view/page/events/<int:eventsPage>')
@admin_required
def viewUser(id, selfActionsPage=1, actionsPage=1, eventsPage=1):
    user = User.get_by_id(id)

    if user:
        selfActions = user.actions \
            .filter(Log.actor_id == Log.user_id) \
            .order_by(Log.timestamp.desc()) \
            .paginate(
                selfActionsPage,
                10,
                True
            )
        otherActions = user.actions \
            .filter(Log.actor_id != Log.user_id) \
            .order_by(Log.timestamp.desc()) \
            .paginate(
                actionsPage,
                10,
                True
            )
        events = user.events \
            .filter(Log.actor_id != Log.user_id) \
            .order_by(Log.timestamp.desc()) \
            .paginate(
                eventsPage,
                10,
                True
            )
    else:
        selfActions = None
        otherActions = None
        events = None

    return render_template(
        'admin/viewUser.html',
        user=user,
        selfActions=selfActions,
        otherActions=otherActions,
        events=events,
        selfActionsPage=selfActionsPage,
        actionsPage=actionsPage,
        eventsPage=eventsPage
    )

@admin.route('/admin/user/<int:id>/impersonate')
@admin_required
def impersonateUser(id):
    user = User.get_by_id(id)

    if user:
        session['actor_id'] = current_user.id

        login_user(
            user,
            remember=False
        )

        log_event(
            'Started impersonating user',
            [],
            user
        )

        return redirect(url_for('dashboard.dashboardHome'))
    else:
        flash(
            u'Could not find user, could not impersonate.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.adminHome'))

@admin.route('/admin/user/<int:id>/give', methods=['POST'])
@admin_required
def giveUser(id):
    user = User.get_by_id(id)

    if user:
        price = (
            int(request.form['givePricePounds']) * 100 +
            int(request.form['givePricePence'])
        )
        numTickets=int(request.form['giveNumTickets'])

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

        for i in xrange(numTickets):
            ticket = Ticket(
                user,
                None,
                price
            )
            ticket.addNote(note)
            tickets.append(ticket)

        db.session.add_all(tickets)
        db.session.commit()

        log_event(
            'Gave {0} tickets'.format(
                numTickets
            ),
            tickets,
            user
        )

        flash(
            u'Gave {0} {1} tickets'.format(
                user.firstname,
                numTickets
            ),
            'success'
        )

        return redirect(request.referrer or url_for('admin.viewUser', id=user.id))
    else:
        flash(
            u'Could not find user, could not give tickets.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.adminHome'))

@admin.route('/admin/user/<int:id>/note', methods=['POST'])
@admin_required
def noteUser(id):
    user = User.get_by_id(id)

    if user:
        user.note = request.form['notes']
        db.session.commit()

        log_event(
            'Updated notes',
            [],
            user
        )

        flash(
            u'Notes set successfully.',
            'success'
        )
        return redirect(request.referrer or url_for('admin.viewUser', id=user.id))
    else:
        flash(
            u'Could not find user, could not set notes.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.adminHome'))

@admin.route('/admin/user/<int:id>/verify')
@admin_required
def verifyUser(id):
    user = User.get_by_id(id)

    if user:
        user.verified = True
        db.session.commit()

        log_event(
            'Verified email',
            [],
            user
        )

        flash(
            u'User marked as verified.',
            'success'
        )
        return redirect(request.referrer or url_for('admin.viewUser', id=user.id))
    else:
        flash(
            u'Could not find user, could not verify.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.adminHome'))

@admin.route('/admin/user/<int:id>/demote')
@admin_required
def demoteUser(id):
    user = User.get_by_id(id)

    if user:
        user.demote()
        db.session.commit()

        log_event(
            'Demoted user',
            [],
            user
        )

        flash(
            u'User demoted.',
            'success'
        )
        return redirect(request.referrer or url_for('admin.viewUser', id=user.id))
    else:
        flash(
            u'Could not find user, could not demote.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.adminHome'))

@admin.route('/admin/user/<int:id>/promote')
@admin_required
def promoteUser(id):
    user = User.get_by_id(id)

    if user:
        user.promote()
        db.session.commit()

        log_event(
            'Promoted user',
            [],
            user
        )

        flash(
            u'User promoted.',
            'success'
        )
        return redirect(request.referrer or url_for('admin.viewUser', id=user.id))
    else:
        flash(
            u'Could not find user, could not promote.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.adminHome'))

@admin.route('/admin/user/<int:id>/collect', methods=['GET','POST'])
@admin_required
def collectTickets(id):
    user = User.get_by_id(id)

    if user:
        return render_template(
            'admin/collectTickets.html',
            user=user
        )
    else:
        flash(
            u'Could not find user, could not process ticket collection.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.adminHome'))

@admin.route('/admin/ticket/<int:id>/view')
@admin.route('/admin/ticket/<int:id>/view/page/<int:eventsPage>')
@admin_required
def viewTicket(id, eventsPage=1):
    ticket = Ticket.get_by_id(id)

    if ticket:
        events = ticket.log_entries \
            .paginate(
                eventsPage,
                10,
                True
            )
    else:
        events = None

    return render_template(
        'admin/viewTicket.html',
        ticket=ticket,
        events=events,
        eventsPage=eventsPage
    )

@admin.route('/admin/ticket/<int:id>/collect', methods=['POST'])
@admin_required
def collectTicket(id):
    ticket = Ticket.get_by_id(id)

    if ticket:
        ticket.barcode = request.form['barcode']
        ticket.collected = True
        db.session.commit()

        log_event(
            'Collected',
            [ticket]
        )

        flash(
            u'Ticket marked as collected with barcode number {0}.'.format(
                request.form['barcode']
            ),
            'success'
        )
        return redirect(request.referrer or url_for('admin.collectTickets', id=ticket.owner_id))
    else:
        flash(
            u'Could not find ticket, could mark as collected.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.adminHome'))

@admin.route('/admin/ticket/<int:id>/note', methods=['POST'])
@admin_required
def noteTicket(id):
    ticket = Ticket.get_by_id(id)

    if ticket:
        ticket.note = request.form['notes']
        db.session.commit()

        log_event(
            'Updated notes',
            [ticket]
        )

        flash(
            u'Notes set successfully.',
            'success'
        )
        return redirect(request.referrer or url_for('admin.viewTicket', id=ticket.id))
    else:
        flash(
            u'Could not find ticket, could not set notes.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.adminHome'))

@admin.route('/admin/ticket/<int:id>/markpaid')
@admin_required
def markTicketPaid(id):
    ticket = Ticket.get_by_id(id)

    if ticket:
        ticket.paid = True
        db.session.commit()

        log_event(
            'Marked as paid',
            [ticket]
        )

        flash(
            u'Ticket successfully marked as paid.',
            'success'
        )
        return redirect(request.referrer or url_for('admin.viewTicket', id=ticket.id))
    else:
        flash(
            u'Could not find ticket, could not mark as paid.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.adminHome'))

@admin.route('/admin/ticket/<int:id>/autocancel')
@admin_required
def autoCancelTicket(id):
    ticket = Ticket.get_by_id(id)

    if ticket:
        if not ticket.canBeCancelledAutomatically():
            flash(
                u'Could not automatically cancel ticket.',
                'warning'
            )
            return redirect(request.referrer or url_for('admin.viewTicket', id=ticket.id))

        if ticket.paymentmethod == 'Battels':
            ticket.battels.cancel(ticket)
        elif ticket.paymentmethod == 'Card':
            refundResult = ticket.card_transaction.processRefund(ticket.price)
            if not refundResult:
                flash(
                    u'Could not process card refund.',
                    'warning'
                )
                return redirect(request.referrer or url_for('admin.viewTicket', id=ticket.id))

        ticket.cancelled = True
        db.session.commit()

        log_event(
            'Cancelled and refunded ticket',
            [ticket]
        )

        flash(
            u'Ticket cancelled successfully.',
            'success'
        )
        return redirect(request.referrer or url_for('admin.viewTicket', id=ticket.id))
    else:
        flash(
            u'Could not find ticket, could not cancel.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.adminHome'))

@admin.route('/admin/ticket/<int:id>/cancel')
@admin_required
def cancelTicket(id):
    ticket = Ticket.get_by_id(id)

    if ticket:
        ticket.cancelled = True
        db.session.commit()

        log_event(
            'Marked ticket as cancelled',
            [ticket]
        )

        flash(
            u'Ticket cancelled successfully.',
            'success'
        )
        return redirect(request.referrer or url_for('admin.viewTicket', id=ticket.id))
    else:
        flash(
            u'Could not find ticket, could not cancel.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.adminHome'))

@admin.route('/admin/ticket/validate', methods=['POST', 'GET'])
@admin_required
def validateTicket():
    valid = None
    message = None

    if request.method == 'POST':
        ticket = Ticket.query.filter(Ticket.barcode==request.form['barcode']).first()

        if not ticket:
            valid = False
            message = "No such ticket with barcode {0}".format(request.form['barcode'])
        elif ticket.entered:
            valid = False
            message = (
                "Ticket has already been used for "
                "entry. Check ID against {0}"
            ).format(ticket.name)
        else:
            ticket.entered = True
            db.session.commit()
            valid = True
            message = "Permit entry for {0}".format(ticket.name)

    return render_template(
        'admin/validateTicket.html',
        valid=valid,
        message=message
    )

@admin.route('/admin/log/<int:id>/view')
@admin_required
def viewLog(id):
    log = Log.get_by_id(id)

    return render_template(
        'admin/viewLog.html',
        log=log
    )

@admin.route('/admin/transaction/<int:id>/view')
@admin.route('/admin/transaction/<int:id>/view/page/<int:eventsPage>')
@admin_required
def viewTransaction(id, eventsPage=1):
    transaction = CardTransaction.get_by_id(id)

    if transaction:
        events = transaction.events \
            .paginate(
                eventsPage,
                10,
                True
            )
    else:
        events = None

    return render_template(
        'admin/viewTransaction.html',
        transaction=transaction,
        events=events,
        eventsPage=eventsPage
    )

@admin.route('/admin/transaction/<int:id>/refund', methods=['POST'])
@admin_required
def refundTransaction(id):
    transaction = CardTransaction.get_by_id(id)

    if transaction:
        amount = int(request.form['refundAmountPounds']) * 100 + int(request.form['refundAmountPence'])

        if amount > (transaction.getValue() - transaction.refunded):
            flash(
                u'Cannot refund more than has been charged.',
                'warning'
            )
            return redirect(request.referrer or url_for('admin.viewTransaction', id=transaction.id))

        result = transaction.processRefund(amount)

        if not result:
            flash(
                u'Could not process refund.',
                'warning'
            )
        else:flash(
                u'Refund processed successfully.',
                'success'
            )
        return redirect(request.referrer or url_for('admin.viewTransaction', id=transaction.id))
    else:
        flash(
            u'Could not find transaction, could not cancel.',
            'warning'
        )
        return redirect(request.referrer or url_for('admin.adminHome'))

@admin.route('/admin/statistics')
@admin_required
def statistics():
    totalValue = db.session \
        .query(func.sum(Ticket.price)) \
        .filter(Ticket.cancelled != True) \
        .scalar()

    if totalValue is None:
        totalValue = 0

    paidValue = db.session \
        .query(func.sum(Ticket.price)) \
        .filter(Ticket.paid == True) \
        .filter(Ticket.cancelled != True) \
        .scalar()

    if paidValue is None:
        paidValue = 0

    cancelledValue = db.session \
        .query(func.sum(Ticket.price)) \
        .filter(Ticket.cancelled == True) \
        .scalar()

    if cancelledValue is None:
        cancelledValue = 0

    paymentMethodValues = db.session \
        .query(func.sum(Ticket.price), Ticket.paymentmethod) \
        .filter(Ticket.cancelled != True) \
        .group_by(Ticket.paymentmethod) \
        .all()

    return render_template(
        'admin/statistics.html',
        totalValue=totalValue,
        paidValue=paidValue,
        cancelledValue=cancelledValue,
        paymentMethodValues=paymentMethodValues
    )

@admin.route('/admin/announcements', methods=['GET','POST'])
@admin.route('/admin/announcements/page/<int:page>', methods=['GET','POST'])
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

            send_email = 'sendEmails' in form and form['sendEmails'] == 'yes'

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

            db.session.add(announcement)
            db.session.commit()

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

@admin.route('/admin/announcement/<int:id>/delete')
@admin_required
def deleteAnnouncement(id):
    announcement = Announcement.get_by_id(id)

    if announcement:
        db.session.delete(announcement)
        db.session.commit()

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

@admin.route('/admin/announcement/<int:id>/cancel')
@admin_required
def cancelAnnouncementEmails(id):
    announcement = Announcement.get_by_id(id)

    if announcement:
        announcement.emails = []
        announcement.send_email = False
        db.session.commit()

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

@admin.route('/admin/vouchers', methods=['GET','POST'])
@admin.route('/admin/vouchers/page/<int:page>', methods=['GET','POST'])
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
            value = int(form['fixedPricePounds']) * 100 + int(form['fixedPricePence'])
        elif form['voucherType'] == 'Fixed Discount':
            value = int(form['fixedDiscountPounds']) * 100 + int(form['fixedDiscountPence'])
        else:
            value = int(form['fixedDiscount'])
            if value > 100:
                flash(
                    u'Cannot give greater than 100% discount',
                    'warning'
                )
                success = False

        if not re.match('[a-zA-Z0-9]+',form['voucherPrefix']):
            flash(
                u'Voucher prefix must be non-empty and contain only letters and numbers',
                'warning'
            )
            success = False

        if success:
            numVouchers = int(form['numVouchers'])
            singleUse = 'singleUse' in form and form['singleUse'] == 'yes'

            for i in xrange(numVouchers):
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
                    singleUse
                )
                db.session.add(voucher)

            db.session.commit()

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

@admin.route('/admin/voucher/<int:id>/delete')
@admin_required
def deleteVoucher(id):
    voucher = Voucher.get_by_id(id)

    if voucher:
        db.session.delete(voucher)
        db.session.commit()
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

@admin.route('/admin/waiting/<int:id>/delete')
@admin_required
def deleteWaiting(id):
    waiting = Waiting.get_by_id(id)

    if waiting:
        db.session.delete(waiting)
        db.session.commit()
        flash(
            u'Waiting list entry deleted',
            'success'
        )
    else:
        flash(
            u'Waiting list entry not found, could not delete.',
            'error'
        )

    return redirect(request.referrer or url_for('admin.adminHome'))

@admin.route('/admin/graphs/sales')
@admin_required
def graphSales():
    statistics = Statistic.query \
        .filter(Statistic.group == 'Sales') \
        .order_by(Statistic.timestamp) \
        .all()

    statisticKeys = [
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
        } for (key, line) in statisticKeys
    }

    for statistic in statistics:
        plots[statistic.statistic]['timestamps'].append(statistic.timestamp)
        plots[statistic.statistic]['datapoints'].append(statistic.value)
        plots[statistic.statistic]['currentValue'] = statistic.value

    return create_plot(plots, statistics[0].timestamp, statistics[-1].timestamp)

@admin.route('/admin/graphs/colleges')
@admin_required
def graphColleges():
    statistics = Statistic.query \
        .filter(Statistic.group == 'Colleges') \
        .order_by(Statistic.timestamp) \
        .all()

    statisticKeys = [
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
        ("None", "c*-"),
        ("Nuffield", "m*-"),
        ("Oriel", "y*-"),
        ("Other", "r+-"),
        ("Pembroke", "g+-"),
        ("Queen's", "b+-"),
        ("Regent's Park", "c+-"),
        ("Somerville", "m+-"),
        ("St Anne's", "y+-"),
        ("St Antony's", "rx-"),
        ("St Benet's Hall", "gx-"),
        ("St Catherine's", "bx-"),
        ("St Cross", "cx-"),
        ("St Edmund Hall", "mx-"),
        ("St Hilda's", "yx-"),
        ("St Hugh's", "rD-"),
        ("St John's", "gD-"),
        ("St Peter's", "bD-"),
        ("St Stephen's House", "cD-"),
        ("Trinity", "mD-"),
        ("University", "yD-"),
        ("Wadham", "rH-"),
        ("Wolfson", "gH-"),
        ("Worcester", "bH-"),
        ("Wycliffe Hall", "cH-")
    ]

    plots = {
        key: {
            'timestamps': [],
            'datapoints': [],
            'line': line,
            'currentValue': 0
        } for (key, line) in statisticKeys
    }

    for statistic in statistics:
        plots[statistic.statistic]['timestamps'].append(statistic.timestamp)
        plots[statistic.statistic]['datapoints'].append(statistic.value)
        plots[statistic.statistic]['currentValue'] = statistic.value

    return create_plot(plots, statistics[0].timestamp, statistics[-1].timestamp)

@admin.route('/admin/graphs/payments')
@admin_required
def graphPayments():
    statistics = Statistic.query \
        .filter(Statistic.group == 'Payments') \
        .order_by(Statistic.timestamp) \
        .all()

    statisticKeys = [
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
        } for (key, line) in statisticKeys
    }

    for statistic in statistics:
        plots[statistic.statistic]['timestamps'].append(statistic.timestamp)
        plots[statistic.statistic]['datapoints'].append(statistic.value)
        plots[statistic.statistic]['currentValue'] = statistic.value

    return create_plot(plots, statistics[0].timestamp, statistics[-1].timestamp)

@admin.route('/admin/data/<group>')
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

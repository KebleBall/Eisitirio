# coding: utf-8
from flask import Blueprint, render_template, request, flash, send_file, redirect, url_for

from kebleball.app import app
from kebleball.helpers.login_manager import admin_required
from kebleball.database import db
from kebleball.database.user import User
from kebleball.database.college import College
from kebleball.database.affiliation import Affiliation
from kebleball.database.ticket import Ticket
from kebleball.database.log import Log
from kebleball.database.statistic import Statistic
from kebleball.database.waiting import Waiting
from kebleball.database.card_transaction import CardTransaction
from sqlalchemy.sql import text
from dateutil.parser import parse
from kebleball.helpers.statistic_plots import create_plot
from StringIO import StringIO
import csv

log = app.log_manager.log_admin

admin = Blueprint('admin', __name__)

@admin.route('/admin', methods=['GET', 'POST'])
@admin.route('/admin/<int:page>', methods=['GET', 'POST'])
@admin_required
def adminHome(page=1):
    userResults = []
    ticketResults = []
    logResults = []
    canGoForwards = False
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

            userQuery = userQuery.limit(numPerPage)
            userQuery = userQuery.offset(numPerPage * (page - 1))
            userResults = userQuery.all()
            canGoForwards = (len(userResults) == numPerPage)
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

            ticketQuery = ticketQuery.limit(numPerPage)
            ticketQuery = ticketQuery.offset(numPerPage * (page - 1))
            ticketResults = ticketQuery.all()
            canGoForwards = (len(ticketResults) == numPerPage)
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

            logQuery = logQuery.limit(numPerPage)
            logQuery = logQuery.offset(numPerPage * (page - 1))
            logResults = logQuery.all()
            canGoForwards = (len(logResults) == numPerPage)

    return render_template(
        'admin/adminHome.html',
        form=form,
        colleges = College.query.all(),
        affiliations = Affiliation.query.all(),
        userResults=userResults,
        ticketResults=ticketResults,
        logResults=logResults,
        ranQuery=(request.method == 'POST'),
        currentPage=page,
        canGoForwards=canGoForwards
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
            .paginate(
                selfActionsPage,
                10,
                True
            )
        otherActions = user.actions \
            .filter(Log.actor_id != Log.user_id) \
            .paginate(
                actionsPage,
                10,
                True
            )
        events = user.events \
            .filter(Log.actor_id != Log.user_id) \
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
    raise NotImplementedError('impersonateUser')

@admin.route('/admin/user/<int:id>/give')
@admin_required
def giveUser(id):
    raise NotImplementedError('giveUser')

@admin.route('/admin/user/<int:id>/note')
@admin_required
def noteUser(id):
    raise NotImplementedError('noteUser')

@admin.route('/admin/user/<int:id>/verify')
@admin_required
def verifyUser(id):
    raise NotImplementedError('verifyUser')

@admin.route('/admin/user/<int:id>/demote')
@admin_required
def demoteUser(id):
    raise NotImplementedError('demoteUser')

@admin.route('/admin/user/<int:id>/promote')
@admin_required
def promoteUser(id):
    raise NotImplementedError('promoteUser')

@admin.route('/admin/ticket/<int:id>/view')
@admin_required
def viewTicket(id):
    ticket = Ticket.get_by_id(id)

    return render_template(
        'admin/viewTicket.html',
        ticket=ticket
    )

@admin.route('/admin/ticket/collect')
@admin_required
def collectTicket():
    raise NotImplementedError('collectTicket')

@admin.route('/admin/log/<int:id>/view')
@admin_required
def viewLog(id):
    log = Log.get_by_id(id)

    return render_template(
        'admin/viewLog.html',
        log=log
    )

@admin.route('/admin/transaction/<int:id>/view')
@admin_required
def viewTransaction(id):
    transaction = CardTransaction.get_by_id(id)

    return render_template(
        'admin/viewTransaction.html',
        transaction=transaction
    )

@admin.route('/admin/statistics')
@admin_required
def statistics():
    return render_template('admin/statistics.html')

@admin.route('/admin/announcements')
@admin_required
def announcements():
    # [todo] - Add announcements
    raise NotImplementedError('announcements')

@admin.route('/admin/vouchers')
@admin_required
def vouchers():
    # [todo] - Add vouchers
    raise NotImplementedError('vouchers')

@admin.route('/admin/delete/waiting/<int:id>')
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

    return redirect(request.referrer or url_for(admin.adminHome))

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
    return send_file(csvdata, mimetype="text/csv")
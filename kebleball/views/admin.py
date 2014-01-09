# coding: utf-8
from flask import Blueprint, render_template, request, flash

from kebleball.app import app
from kebleball.helpers.login_manager import admin_required
from kebleball.database.user import User
from kebleball.database.college import College
from kebleball.database.affiliation import Affiliation
from kebleball.database.ticket import Ticket
from kebleball.database.log import Log
from sqlalchemy.sql import text
from dateutil.parser import parse

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

@admin.route('/admin/view/user/<int:id>')
@admin_required
def viewUser(id):
    # [todo] - Add viewUser
    raise NotImplementedError('viewUser')

@admin.route('/admin/view/ticket/<int:id>')
@admin_required
def viewTicket(id):
    # [todo] - Add viewTicket
    raise NotImplementedError('viewTicket')

@admin.route('/admin/view/log/<int:id>')
@admin_required
def viewLog(id):
    # [todo] - Add viewLog
    raise NotImplementedError('viewLog')

@admin.route('/admin/view/transaction/<int:id>')
@admin_required
def viewTransaction(id):
    # [todo] - Add viewTransaction
    raise NotImplementedError('viewTransaction')

@admin.route('/admin/statistics')
@admin_required
def statistics():
    # [todo] - Add statistics
    raise NotImplementedError('statistics')

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

@admin.route('/admin/graphs/sales')
@admin_required
def graphSales():
    # [todo] - Add graphSales
    raise NotImplementedError('graphSales')

@admin.route('/admin/graphs/colleges')
@admin_required
def graphColleges():
    # [todo] - Add graphColleges
    raise NotImplementedError('graphColleges')

@admin.route('/admin/graphs/payments')
@admin_required
def graphPayments():
    # [todo] - Add graphPayments
    raise NotImplementedError('graphPayments')

@admin.route('/admin/data/sales')
@admin_required
def dataSales():
    # [todo] - Add dataSales
    raise NotImplementedError('dataSales')

@admin.route('/admin/data/colleges')
@admin_required
def dataColleges():
    # [todo] - Add dataColleges
    raise NotImplementedError('dataColleges')

@admin.route('/admin/data/payments')
@admin_required
def dataPayments():
    # [todo] - Add dataPayments
    raise NotImplementedError('dataPayments')
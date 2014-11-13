# coding: utf-8
from flask import Blueprint, request, render_template, redirect, flash, url_for
from flask.ext.login import login_required, current_user

from kebleball.app import app
from kebleball.database import db
from kebleball.database.user import User
from kebleball.database.ticket import Ticket

log = app.log_manager.log_resale

RESALE = Blueprint('resale', __name__)

@RESALE.route('/resale', methods=['GET','POST'])
@login_required
def resaleHome():
    if request.method == 'POST':
        tickets = Ticket.query \
            .filter(Ticket.id.in_(request.form.getlist('tickets[]'))) \
            .filter(Ticket.owner_id == current_user.id) \
            .filter(Ticket.paid == True) \
            .all()

        while None in tickets:
            tickets.remove(None)

        resale_to = User.get_by_email(request.form['resaleEmail'])

        if not resale_to:
            flash(
                u'No user with that email exists'
                'error'
            )
            return(render_template('resale/resaleHome.html'))
        elif resale_to == current_user:
            flash(
                u"You can't resell tickets to yourself",
                'info'
            )
            return(render_template('resale/resaleHome.html'))

        Ticket.start_resale(tickets, resale_to)

        flash(
            u'The resale process has been started',
            'info'
        )

    return(render_template('resale/resaleHome.html'))

@RESALE.route('/resale/cancel', methods=['GET','POST'])
@login_required
def cancelResale():
    if request.method == 'POST':
        tickets = Ticket.query \
            .filter(Ticket.id.in_(request.form.getlist('tickets[]'))) \
            .filter(Ticket.owner_id == current_user.id) \
            .filter(Ticket.paid == True) \
            .all()

        for ticket in tickets:
            if not ticket:
                continue

            ticket.resalekey = None
            ticket.resaleconfirmed = None
            ticket.reselling_to = None
            ticket.reselling_to_id = None

        db.session.commit()

        flash(
            u'The tickets have been removed from resale',
            'success'
        )

    return(render_template('resale/cancelResale.html'))

@RESALE.route('/resale/confirm/<int:resale_from>/<int:resale_to>/<key>')
@login_required
def resaleConfirm(resale_from, resale_to, key):
    if Ticket.confirm_resale(resale_from, resale_to, key):
        flash(
            (
                u'The resale arrangement has been confirmed. '
                u'You must now arrange payment'
            ),
            'info'
        )
    else:
        flash(
            (
                u'An error occurred, and the resale could not be confirmed. '
                u'If the error persists, please contact <a href="{0}" '
                u'target="_blank">the webmaster</a>.'
            ).format(
                app.config['WEBSITE_EMAIL_LINK']
            ),
            'warning'
        )

    return redirect(url_for('dashboard.dashboardHome'))

@RESALE.route('/resale/complete/<int:resale_from>/<int:resale_to>/<key>')
@login_required
def resaleComplete(resale_from, resale_to, key):
    if Ticket.complete_resale(resale_from, resale_to, key):
        flash(
            (
                u'The resale arrangement has been completed, and the tickets '
                u'have been transferred.'
            ),
            'success'
        )
    else:
        flash(
            (
                u'An error occurred, and the resale could not be completed. '
                u'If the error persists, please contact <a href="{0}" '
                u'target="_blank">the webmaster</a>.'
            ).format(
                app.config['WEBSITE_EMAIL_LINK']
            ),
            'warning'
        )

    return redirect(url_for('dashboard.dashboardHome'))

@RESALE.route('/resale/cancel/<int:resale_from>/<int:resale_to>/<key>')
@login_required
def resaleCancel(resale_from, resale_to, key):
    if Ticket.cancel_resale(resale_from, resale_to, key):
        flash(
            u'The resale arrangement has been cancelled.',
            'info'
        )
    else:
        flash(
            (
                u'An error occurred, and the resale could not be cancelled. '
                u'If the error persists, please contact <a href="{0}" '
                u'target="_blank">the webmaster</a>.'
            ).format(
                app.config['WEBSITE_EMAIL_LINK']
            ),
            'warning'
        )

    return redirect(url_for('dashboard.dashboardHome'))

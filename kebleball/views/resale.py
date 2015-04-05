# coding: utf-8
"""Views related to reselling tickets to other users."""

from flask import Blueprint, request, render_template, redirect, flash, url_for
from flask.ext.login import login_required, current_user

from kebleball import app
from kebleball.database import db
from kebleball.database import models

APP = app.APP
DB = db.DB

RESALE = Blueprint('resale', __name__)

@RESALE.route('/resale', methods=['GET', 'POST'])
@login_required
def resale_home():
    """Start the resale process.

    Presents the user with a list of their tickets (which must have been paid
    for) with checkboxes, allowing them to select tickets and sell them to
    another user. The resale process involves 4 steps:
        1. The sender selects which tickets they want to resell, and enters the
            email address of the recipient
        2. The recipient receives an email containing a link which they must
            click to confirm they want the tickets, and a link to say they don't
        3. The sender receives an email saying the recipient does want the
            tickets, and that they should collect payment from them. This email
            contains a link to click when the payment is completed, and a link
            to cancel the process
        4. Once the sender has been paid, they click the link to confirm this,
            and the tickets are transferred to the recipient's account
    """
    if request.method == 'POST':
        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(request.form.getlist('tickets[]'))
        ).filter(
            models.Ticket.owner_id == current_user.object_id
        ).filter(
            models.Ticket.paid == True
        ).all()

        while None in tickets:
            tickets.remove(None)

        resale_to = models.User.get_by_email(request.form['resaleEmail'])

        if not resale_to:
            flash(
                u'No user with that email exists'
                'error'
            )
            return render_template('resale/resaleHome.html')
        elif resale_to == current_user:
            flash(
                u'You can\'t resell tickets to yourself',
                'info'
            )
            return render_template('resale/resaleHome.html')

        models.Ticket.start_resale(tickets, resale_to)

        flash(
            u'The resale process has been started',
            'info'
        )

    return render_template('resale/resaleHome.html')

@RESALE.route('/resale/cancel', methods=['GET', 'POST'])
@login_required
def cancel_resale():
    """Allow a user to cancel the resale of tickets they own.

    Presents the user with a list of tickets they are reselling, and allows them
    to cancel the resale process for any of them.
    """
    if request.method == 'POST':
        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(request.form.getlist('tickets[]'))
        ).filter(
            models.Ticket.owner_id == current_user.object_id
        ).filter(
            models.Ticket.paid == True
        ).all()

        for ticket in tickets:
            if not ticket:
                continue

            ticket.resale_key = None
            ticket.resaleconfirmed = None
            ticket.reselling_to = None
            ticket.reselling_to_id = None

        DB.session.commit()

        flash(
            u'The tickets have been removed from resale',
            'success'
        )

    return render_template('resale/cancelResale.html')

@RESALE.route('/resale/confirm/<int:resale_from>/<int:resale_to>/<key>')
@login_required
def resale_confirm(resale_from, resale_to, key):
    """Confirm the resale process.

    Linked to in the confirmation email, completes step 2 above and starts step
    3.
    """
    if models.Ticket.confirm_resale(resale_from, resale_to, key):
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
                APP.config['WEBSITE_EMAIL_LINK']
            ),
            'warning'
        )

    return redirect(url_for('dashboard.dashboard_home'))

@RESALE.route('/resale/complete/<int:resale_from>/<int:resale_to>/<key>')
@login_required
def resale_complete(resale_from, resale_to, key):
    """Complete the resale process.

    Linked to in the completion email, completes step 3 above and starts step 4.
    """
    if models.Ticket.complete_resale(resale_from, resale_to, key):
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
                APP.config['WEBSITE_EMAIL_LINK']
            ),
            'warning'
        )

    return redirect(url_for('dashboard.dashboard_home'))

@RESALE.route('/resale/cancel/<int:resale_from>/<int:resale_to>/<key>')
@login_required
def resale_cancel(resale_from, resale_to, key):
    """Cancel the resale process.

    Linked to in both the confirmation and completion emails, cancels the resale
    process.
    """
    if models.Ticket.cancel_resale(resale_from, resale_to, key):
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
                APP.config['WEBSITE_EMAIL_LINK']
            ),
            'warning'
        )

    return redirect(url_for('dashboard.dashboard_home'))

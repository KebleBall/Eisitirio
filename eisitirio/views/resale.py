# coding: utf-8
"""Views related to reselling tickets to other users."""

from __future__ import unicode_literals

from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

APP = app.APP
DB = db.DB

RESALE = flask.Blueprint('resale', __name__)

@RESALE.route('/resale', methods=['GET', 'POST'])
@login.login_required
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
    if flask.request.method == 'POST':
        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(flask.request.form.getlist('tickets[]'))
        ).filter(
            models.Ticket.owner_id == login.current_user.object_id
        ).filter(
            models.Ticket.paid == True
        ).all()

        resale_to = models.User.get_by_email(flask.request.form['resale_email'])

        if not resale_to:
            flask.flash(
                'No user with that email exists',
                'error'
            )
            return flask.render_template('resale/resale_home.html')
        elif resale_to == login.current_user:
            flask.flash(
                'You can\'t resell tickets to yourself',
                'info'
            )
            return flask.render_template('resale/resale_home.html')

        models.Ticket.start_resale(tickets, resale_to)

        flask.flash(
            'The resale process has been started',
            'info'
        )

    return flask.render_template('resale/resale_home.html')

@RESALE.route('/resale/cancel', methods=['GET', 'POST'])
@login.login_required
def cancel_resale():
    """Allow a user to cancel the resale of tickets they own.

    Presents the user with a list of tickets they are reselling, and allows them
    to cancel the resale process for any of them.
    """
    if flask.request.method == 'POST':
        tickets = models.Ticket.query.filter(
            models.Ticket.object_id.in_(flask.request.form.getlist('tickets[]'))
        ).filter(
            models.Ticket.owner_id == login.current_user.object_id
        ).filter(
            models.Ticket.paid == True
        ).all()

        for ticket in tickets:
            ticket.resale_key = None
            ticket.resaleconfirmed = None
            ticket.reselling_to = None
            ticket.reselling_to_id = None

        DB.session.commit()

        flask.flash(
            'The tickets have been removed from resale',
            'success'
        )

    return flask.render_template('resale/cancel_resale.html')

@RESALE.route('/resale/confirm/<int:resale_from>/<int:resale_to>/<key>')
@login.login_required
def resale_confirm(resale_from, resale_to, key):
    """Confirm the resale process.

    Linked to in the confirmation email, completes step 2 above and starts step
    3.
    """
    if models.Ticket.confirm_resale(resale_from, resale_to, key):
        flask.flash(
            (
                'The resale arrangement has been confirmed. '
                'You must now arrange payment'
            ),
            'info'
        )
    else:
        flask.flash(
            (
                'An error occurred, and the resale could not be confirmed. '
                'If the error persists, please contact <a href="{0}" '
                'target="_blank">the webmaster</a>.'
            ).format(
                APP.config['WEBSITE_EMAIL_LINK']
            ),
            'warning'
        )

    return flask.redirect(flask.url_for('dashboard.dashboard_home'))

@RESALE.route('/resale/complete/<int:resale_from>/<int:resale_to>/<key>')
@login.login_required
def resale_complete(resale_from, resale_to, key):
    """Complete the resale process.

    Linked to in the completion email, completes step 3 above and starts step 4.
    """
    if models.Ticket.complete_resale(resale_from, resale_to, key):
        flask.flash(
            (
                'The resale arrangement has been completed, and the tickets '
                'have been transferred.'
            ),
            'success'
        )
    else:
        flask.flash(
            (
                'An error occurred, and the resale could not be completed. '
                'If the error persists, please contact <a href="{0}" '
                'target="_blank">the webmaster</a>.'
            ).format(
                APP.config['WEBSITE_EMAIL_LINK']
            ),
            'warning'
        )

    return flask.redirect(flask.url_for('dashboard.dashboard_home'))

@RESALE.route('/resale/cancel/<int:resale_from>/<int:resale_to>/<key>')
@login.login_required
def resale_cancel(resale_from, resale_to, key):
    """Cancel the resale process.

    Linked to in both the confirmation and completion emails, cancels the resale
    process.
    """
    if models.Ticket.cancel_resale(resale_from, resale_to, key):
        flask.flash(
            'The resale arrangement has been cancelled.',
            'info'
        )
    else:
        flask.flash(
            (
                'An error occurred, and the resale could not be cancelled. '
                'If the error persists, please contact <a href="{0}" '
                'target="_blank">the webmaster</a>.'
            ).format(
                APP.config['WEBSITE_EMAIL_LINK']
            ),
            'warning'
        )

    return flask.redirect(flask.url_for('dashboard.dashboard_home'))

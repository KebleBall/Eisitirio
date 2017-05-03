# coding: utf-8
"""Views related to administrative tasks performed on tickets."""

from __future__ import unicode_literals

import flask_login as login
# from flask.ext import login
import flask
import base64

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import login_manager
from eisitirio.logic import cancellation_logic
from eisitirio.scripts import create_qr_codes

APP = app.APP
DB = db.DB

ADMIN_TICKETS = flask.Blueprint('admin_tickets', __name__)

@ADMIN_TICKETS.route('/admin/ticket/<int:ticket_id>/view')
@ADMIN_TICKETS.route(
    '/admin/ticket/<int:ticket_id>/view/page/<int:events_page>'
)
@login.login_required
@login_manager.admin_required
def view_ticket(ticket_id, events_page=1):
    """View a ticket object."""
    ticket = models.Ticket.get_by_id(ticket_id)

    if ticket:
        events = ticket.events.paginate(
            events_page,
            10,
            True
        )
    else:
        events = None

    return flask.render_template(
        'admin_tickets/view_ticket.html',
        ticket=ticket,
        events=events,
        events_page=events_page
    )

@ADMIN_TICKETS.route('/admin/ticket/<int:ticket_id>/note',
                     methods=['GET', 'POST'])
@login.login_required
@login_manager.admin_required
def note_ticket(ticket_id):
    """Set notes for a ticket."""
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

    ticket = models.Ticket.get_by_id(ticket_id)

    if ticket:
        ticket.note = flask.request.form['notes']
        DB.session.commit()

        APP.log_manager.log_event(
            'Updated notes',
            tickets=[ticket]
        )

        flask.flash(
            'Notes set successfully.',
            'success'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_tickets.view_ticket',
                                            ticket_id=ticket.object_id))
    else:
        flask.flash(
            'Could not find ticket, could not set notes.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_TICKETS.route('/admin/ticket/<int:ticket_id>/markpaid')
@login.login_required
@login_manager.admin_required
def mark_ticket_paid(ticket_id):
    """Mark a ticket as paid.

    Generally used for tickets being paid for by cash/cheque, but also used if
    something goes wrong and the ticket isn't correctly marked as paid.
    """
    ticket = models.Ticket.get_by_id(ticket_id)

    if ticket:
        ticket.paid = True
        DB.session.commit()

        APP.log_manager.log_event(
            'Marked as paid',
            tickets=[ticket]
        )

        flask.flash(
            'Ticket successfully marked as paid.',
            'success'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_tickets.view_ticket',
                                            ticket_id=ticket.object_id))
    else:
        flask.flash(
            'Could not find ticket, could not mark as paid.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_TICKETS.route('/admin/ticket/<int:ticket_id>/autocancel')
@login.login_required
@login_manager.admin_required
def refund_ticket(ticket_id):
    """Cancel and refund a ticket.

    Marks a ticket as cancelled, and refunds the money to the owner via the
    original payment method (where possible).
    """
    ticket = models.Ticket.get_by_id(ticket_id)

    if ticket:
        if not ticket.can_be_cancelled():
            flask.flash(
                'Could not automatically cancel ticket.',
                'warning'
            )
            return flask.redirect(flask.request.referrer or
                                  flask.url_for('admin_tickets.view_ticket',
                                                ticket_id=ticket.object_id))

        if cancellation_logic.cancel_tickets([ticket], quiet=True):
            flask.flash('Ticket was cancelled and refunded.', 'success')
        else:
            flask.flash('Ticket could not be cancelled/refunded.', 'error')

        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_tickets.view_ticket',
                                            ticket_id=ticket.object_id))
    else:
        flask.flash(
            'Could not find ticket, could not cancel.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_TICKETS.route('/admin/ticket/<int:ticket_id>/cancel')
@login.login_required
@login_manager.admin_required
def cancel_ticket(ticket_id):
    """Cancel a ticket without refunding it."""
    ticket = models.Ticket.get_by_id(ticket_id)

    if ticket:
        ticket.cancelled = True
        DB.session.commit()

        APP.log_manager.log_event(
            'Marked ticket as cancelled',
            tickets=[ticket]
        )

        flask.flash(
            'Ticket cancelled successfully.',
            'success'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_tickets.view_ticket',
                                            ticket_id=ticket.object_id))
    else:
        flask.flash(
            'Could not find ticket, could not cancel.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_TICKETS.route('/admin/ticket/<int:ticket_id>/uncollect')
@login.login_required
@login_manager.admin_required
def uncollect_ticket(ticket_id):
    """Mark a ticket has having not been collected.

    Removes the barcode from the ticket and marks it as not collected. This will
    prevent the wristband with the given barcode from being used to enter the
    ball.
    """
    ticket = models.Ticket.get_by_id(ticket_id)

    if ticket:
        ticket.barcode = None
        DB.session.commit()

        APP.log_manager.log_event(
            'Marked ticket as uncollected',
            tickets=[ticket]
        )

        flask.flash(
            u'Ticket marked as uncollected.',
            'success'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_tickets.view_ticket',
                                            ticket_id=ticket.object_id))
    else:
        flask.flash(
            u'Could not find ticket, could not mark as uncollected.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_TICKETS.route('/admin/ticket/validate', methods=['POST', 'GET'])
@login.login_required
@login_manager.admin_required
def validate_ticket():
    """Validate a ticket upon entry to the ball.

    Wristbands are scanned at guest's entry to the ball, this presents an
    interface for scanning the barcodes and confirming that the barcode is
    valid and has not previously been used to enter the ball.
    """
    valid = None
    message = None
    photo = None

    if flask.request.method == 'POST':
        ticket = models.Ticket.query.filter(
            models.Ticket.barcode == flask.request.form['barcode']).first()

        if not ticket:
            valid = False
            message = 'No such ticket with barcode {0}'.format(
                flask.request.form['barcode'])
        elif ticket.entered:
            valid = False
            message = (
                'Ticket has already been used for '
                'entry. Check ID against {0} (owned by {1})'
            ).format(
                ticket.holder.full_name,
                ticket.owner.full_name
            )
            photo = ticket.holder.photo
        else:
            ticket.entered = True
            DB.session.commit()
            valid = True
            message = 'Permit entry for {0}'.format(ticket.holder.full_name)
            photo = ticket.holder.photo

    return flask.render_template(
        'admin_tickets/validate_ticket.html',
        valid=valid,
        message=message,
        photo=photo
    )

@ADMIN_TICKETS.route('/admin/ticket/validate-ticket/<int:ticket_id>/<string:barcode>', methods=['POST', 'GET'])
@login.login_required
@login_manager.admin_required
def check_ticket(ticket_id, barcode):
    ticket = models.Ticket.get_by_id(ticket_id)

    valid = None
    message = None
    photo = None

    if not ticket:
        valid = False
        message = 'No such ticket with barcode {0}'.format(barcode)

    elif ticket.entered:
        valid = False
        message = (
            'Ticket has already been used for '
            'entry. Check ID against {0} (owned by {1})'
        ).format(
            ticket.holder.full_name,
            ticket.owner.full_name
        )
        photo = ticket.holder.photo.thumb_url
    elif not ticket.holder:
        valid = False
        message = (
            'Ticket has not been claimed. Owner is {0}'
            ).format(ticket.owner.full_name)
        photo = ticket.owner.photo.thumb_url
    else:
        ticket.entered = True
        DB.session.commit()
        valid = True
        message = 'Permit entry for {0}'.format(ticket.holder.full_name)
        photo = ticket.holder.photo.thumb_url

    return flask.jsonify(ticketvalid=valid, message=message,
            photourl=photo)

###########################################################################

@ADMIN_TICKETS.route('/admin/ticket/check-ticket-qrs', methods=['POST', 'GET'])
@login.login_required
@login_manager.admin_required
def check_ticket_qr():
    """A simple little view to make sure all the qrs are working correctly"""

    tickets = models.Ticket.query.filter(
        models.Ticket.barcode != None,
        models.Ticket.holder_id != None
    ).all()

    index = -1

    if flask.request.method == 'POST':
        index = int(flask.request.form['current_ticket_index'])
        if len(tickets) <= index + 1:
            return "Done"

    ticket = tickets[index + 1]
    return flask.render_template(
            'admin_tickets/check_ticket_qrs.html',
            idx=index + 1,
            barcode=base64.b64encode(create_qr_codes.generate_ticket_qr(ticket))
        )


@ADMIN_TICKETS.route('/admin/ticket/test-validate-ticket/<int:ticket_id>/<string:barcode>', methods=['POST', 'GET'])
@login.login_required
@login_manager.admin_required
def test_check_ticket(ticket_id, barcode):
    ticket = models.Ticket.get_by_id(ticket_id)

    valid = None
    message = None
    photo = None

    if not ticket:
        valid = False
        message = 'No such ticket with barcode {0}'.format(barcode)
        # XXX : Need to return a non-null image here
    elif ticket.entered:
        valid = False
        message = (
            'Ticket has already been used for '
            'entry. Check ID against {0} (owned by {1})'
        ).format(
            ticket.holder.full_name.encode('utf-8'),
            ticket.owner.full_name.encode('utf-8')
        )
        photo = ticket.holder.photo.thumb_url
    elif not ticket.holder:
        valid = False
        message = (
            'Ticket has not been claimed. Owner is {0}'
            ).format(ticket.owner.full_name.encode('utf-8'))
        photo = ticket.owner.photo.thumb_url
    elif not ticket.barcode or (ticket.barcode and ticket.barcode != barcode):
        valid = False
        message = 'Found ticket, barcode doesnt match {0}'.format(barcode)
        photo = ticket.holder.photo.thumb_url
    else:
        valid = True
        message = 'Permit entry for {0}'.format(ticket.holder.full_name.encode('utf-8'))
        photo = ticket.holder.photo.thumb_url

    return flask.jsonify(ticketvalid=valid, message=message, photourl=photo)

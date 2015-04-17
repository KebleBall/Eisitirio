# coding: utf-8
"""Views related to administrative tasks performed on tickets."""

from __future__ import unicode_literals

import flask

from kebleball import app
from kebleball.database import db
from kebleball.database import models
from kebleball.helpers import login_manager

APP = app.APP
DB = db.DB

ADMIN_TICKETS = flask.Blueprint('admin_tickets', __name__)

@ADMIN_TICKETS.route('/admin/ticket/<int:ticket_id>/view')
@ADMIN_TICKETS.route(
    '/admin/ticket/<int:ticket_id>/view/page/<int:events_page>'
)
@login_manager.admin_required
def view_ticket(ticket_id, events_page=1):
    """View a ticket object."""
    ticket = models.Ticket.get_by_id(ticket_id)

    if ticket:
        events = ticket.log_entries.paginate(
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

@ADMIN_TICKETS.route('/admin/ticket/<int:ticket_id>/collect',
                     methods=['GET', 'POST'])
@login_manager.admin_required
def collect_ticket(ticket_id):
    """Mark a ticket as collected, and add a barcode.

    Performs the requisite logic to check the barcode submitted for a ticket,
    and marks the ticket as collected.
    """
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

    existing = models.Ticket.query.filter(
        models.Ticket.barcode == flask.request.form['barcode']
    ).count()

    if existing > 0:
        flask.flash(
            'Barcode has already been used for a ticket.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

    ticket = models.Ticket.get_by_id(ticket_id)

    if ticket:
        ticket.barcode = flask.request.form['barcode']
        ticket.collected = True
        DB.session.commit()

        APP.log_manager.log_event(
            'Collected',
            [ticket]
        )

        flask.flash(
            'Ticket marked as collected with barcode number {0}.'.format(
                flask.request.form['barcode']
            ),
            'success'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_users.collect_tickets',
                                            ticket_id=ticket.owner_id))
    else:
        flask.flash(
            'Could not find ticket, could mark as collected.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_TICKETS.route('/admin/ticket/<int:ticket_id>/note',
                     methods=['GET', 'POST'])
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
            [ticket]
        )

        flask.flash(
            'Notes set successfully.',
            'success'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_tickets.view_ticket',
                                            ticket_id=ticket.ticket_id))
    else:
        flask.flash(
            'Could not find ticket, could not set notes.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_TICKETS.route('/admin/ticket/<int:ticket_id>/markpaid')
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
            [ticket]
        )

        flask.flash(
            'Ticket successfully marked as paid.',
            'success'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_tickets.view_ticket',
                                            ticket_id=ticket.ticket_id))
    else:
        flask.flash(
            'Could not find ticket, could not mark as paid.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_TICKETS.route('/admin/ticket/<int:ticket_id>/autocancel')
@login_manager.admin_required
def auto_cancel_ticket(ticket_id):
    """Cancel and refund a ticket.

    Marks a ticket as cancelled, and refunds the money to the owner via the
    original payment method (where possible).
    """
    ticket = models.Ticket.get_by_id(ticket_id)

    if ticket:
        if not ticket.can_be_cancelled_automatically():
            flask.flash(
                'Could not automatically cancel ticket.',
                'warning'
            )
            return flask.redirect(flask.request.referrer or
                                  flask.url_for('admin_tickets.view_ticket',
                                                ticket_id=ticket.ticket_id))

        if ticket.payment_method == 'Battels':
            ticket.battels.cancel(ticket)
        elif ticket.payment_method == 'Card':
            refund_result = ticket.card_transaction.process_refund(ticket.price)
            if not refund_result:
                flask.flash(
                    'Could not process card refund.',
                    'warning'
                )
                return flask.redirect(flask.request.referrer or
                                      flask.url_for('admin_tickets.view_ticket',
                                                    ticket_id=ticket.ticket_id))

        ticket.cancelled = True
        DB.session.commit()

        APP.log_manager.log_event(
            'Cancelled and refunded ticket',
            [ticket]
        )

        flask.flash(
            'Ticket cancelled successfully.',
            'success'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_tickets.view_ticket',
                                            ticket_id=ticket.ticket_id))
    else:
        flask.flash(
            'Could not find ticket, could not cancel.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_TICKETS.route('/admin/ticket/<int:ticket_id>/cancel')
@login_manager.admin_required
def cancel_ticket(ticket_id):
    """Cancel a ticket without refunding it."""
    ticket = models.Ticket.get_by_id(ticket_id)

    if ticket:
        ticket.cancelled = True
        DB.session.commit()

        APP.log_manager.log_event(
            'Marked ticket as cancelled',
            [ticket]
        )

        flask.flash(
            'Ticket cancelled successfully.',
            'success'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_tickets.view_ticket',
                                            ticket_id=ticket.ticket_id))
    else:
        flask.flash(
            'Could not find ticket, could not cancel.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_TICKETS.route('/admin/ticket/validate', methods=['POST', 'GET'])
@login_manager.admin_required
def validate_ticket():
    """Validate a ticket upon entry to the ball.

    Wristbands are scanned at guest's entry to the ball, this presents an
    interface for scanning the barcodes and confirming that the barcode is
    valid and has not previously been used to enter the ball.
    """
    valid = None
    message = None

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
                ticket.name,
                ticket.owner.full_name
            )
        else:
            ticket.entered = True
            DB.session.commit()
            valid = True
            message = 'Permit entry for {0}'.format(ticket.name)

    return flask.render_template(
        'admin_tickets/validate_ticket.html',
        valid=valid,
        message=message
    )

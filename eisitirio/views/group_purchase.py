# coding: utf-8
"""Views related to the group purchase process."""

from __future__ import unicode_literals

from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import util
from eisitirio.logic import purchase_logic

APP = app.APP
DB = db.DB

GROUP_PURCHASE = flask.Blueprint('group_purchase', __name__)

@GROUP_PURCHASE.route('/purchase/group/dashboard')
@login.login_required
def dashboard():
    """Display the group purchase dashboard."""
    if not login.current_user.purchase_group:
        return flask.render_template(
            'group_purchase/dashboard.html'
        )

    return flask.render_template(
        'group_purchase/dashboard.html',
        ticket_info=purchase_logic.get_group_ticket_info(login.current_user)
    )

@GROUP_PURCHASE.route('/purchase/group/create')
@login.login_required
def create():
    """Create a new purchase group."""
    if login.current_user.purchase_group:
        flask.flash('You are already a member of a purchase group', 'error')
    else:
        group = models.PurchaseGroup(login.current_user)

        DB.session.add(group)
        DB.session.commit()

        APP.log_manager.log_event(
            'Created Purchase Group',
            user=login.current_user,
            purchase_group=group
        )

    return flask.redirect(flask.url_for('group_purchase.dashboard'))

@GROUP_PURCHASE.route('/purchase/group/join', methods=['GET', 'POST'])
@login.login_required
def join():
    """Join a pre-existing purchase group."""
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.dashboard_home'))

    if login.current_user.purchase_group:
        flask.flash('You are already a member of a purchase group', 'error')
    else:
        group = None
        if (
                'code' in flask.request.form and
                flask.request.form['code'] != ''
        ):
            group = models.PurchaseGroup.get_by_code(flask.request.form['code'])

        if group:
            if login.current_user.can_join_group(group):
                group.members.append(login.current_user)
                DB.session.commit()

                APP.log_manager.log_event(
                    'Joined Purchase Group',
                    user=login.current_user,
                    purchase_group=group
                )
            else:
                flask.flash(
                    (
                        'You cannot join this group as it has the maximum '
                        'number of members'
                    ),
                    'error'
                )
        else:
            flask.flash('Could not join group', 'error')

    return flask.redirect(flask.url_for('group_purchase.dashboard'))

@GROUP_PURCHASE.route('/purchase/group/disband')
@login.login_required
def disband():
    """Disband a purchase group, cancelling all requests.

    Only the leader of a group can disband it.
    """
    if (
            not login.current_user.purchase_group or
            login.current_user != login.current_user.purchase_group.leader
    ):
        flask.flash('You are not the leader of any purchase group', 'error')
    else:
        group = login.current_user.purchase_group

        group.disbanded = True
        group.members = []

        DB.session.commit()

        APP.log_manager.log_event(
            'Disbanded Purchase Group',
            user=login.current_user,
            purchase_group=group
        )

    return flask.redirect(flask.url_for('group_purchase.dashboard'))

@GROUP_PURCHASE.route('/purchase/group/leave')
@login.login_required
def leave():
    """Leave a purchase group.

    The leader of a group may not leave it.
    """
    if not login.current_user.purchase_group:
        flask.flash('You are not a member of any purchase group', 'error')
    elif login.current_user == login.current_user.purchase_group.leader:
        flask.flash('You can not leave a purchase group you lead', 'error')
    else:
        group = login.current_user.purchase_group

        group.members.remove(login.current_user)

        if not group.purchased:
            for request in login.current_user.group_purchase_requests:
                DB.session.delete(request)

        APP.log_manager.log_event(
            'Left Purchase Group',
            user=login.current_user,
            purchase_group=group
        )

        DB.session.commit()

    return flask.redirect(flask.url_for('group_purchase.dashboard'))

@GROUP_PURCHASE.route('/purchase/group/request', methods=['GET', 'POST'])
@login.login_required
def update_request():
    """Update a group purchase request."""
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('group_purchase.dashboard'))

    ticket_info = purchase_logic.get_group_ticket_info(login.current_user)

    num_tickets = {
        ticket_type.slug: int(
            flask.request.form['num_tickets_{0}'.format(ticket_type.slug)]
        )
        for ticket_type, _ in ticket_info.ticket_types
    }

    flashes = purchase_logic.validate_tickets(ticket_info, num_tickets, [])

    if flashes:
        for flash in flashes:
            flask.flash(flash, 'error')

        return flask.redirect(flask.request.referrer or
                              flask.url_for('group_purchase.dashboard'))

    existing_requests = {
        request.ticket_type_slug: request
        for request in login.current_user.group_purchase_requests
    }

    for slug, request in existing_requests.iteritems():
        if slug not in num_tickets or num_tickets[slug] == 0:
            DB.session.delete(request)

    for slug, requested in num_tickets.iteritems():
        if slug in existing_requests:
            existing_requests[slug].number_requested = requested
        else:
            DB.session.add(models.GroupPurchaseRequest(
                slug,
                requested,
                login.current_user.purchase_group,
                login.current_user
            ))

    DB.session.commit()

    APP.log_manager.log_event(
        'Updated Group Purchase Request',
        user=login.current_user,
        purchase_group=login.current_user.purchase_group
    )

    flask.flash('Your ticket request has been updated.', 'success')

    return flask.redirect(flask.url_for('group_purchase.dashboard'))

@GROUP_PURCHASE.route('/purchase/group/checkout', methods=['GET', 'POST'])
@login.login_required
def checkout():
    """Allow the group leader to purchase tickets on behalf of the group."""
    if not login.current_user.purchase_group:
        flask.flash(
            (
                'You are not currently a member of a purchase group. Please '
                'use the "Buy Tickets" link to purchase tickets individually.'
            ),
            'info'
        )
        return flask.redirect(flask.url_for('dashboard.dashboard_home'))
    elif login.current_user != login.current_user.purchase_group.leader:
        flask.flash(
            (
                'Only your group leader {0} can purchase tickets on behalf of '
                'your purchase group.'
            ).format(login.current_user.purchase_group.leader.full_name),
            'info'
        )
        return flask.redirect(flask.url_for('dashboard.dashboard_home'))
    elif not APP.config['TICKETS_ON_SALE']:
        flask.flash(
            (
                'You will only be able to purchase tickets on behalf of your '
                'purchase group when general release starts.'
            ),
            'info'
        )
        return flask.redirect(flask.url_for('dashboard.dashboard_home'))
    elif login.current_user.purchase_group.purchased:
        flask.flash(
            (
                'The tickets have already been purchased for your purchase '
                'group.'
            ),
            'info'
        )
        return flask.redirect(flask.url_for('dashboard.dashboard_home'))

    guest_tickets_available = purchase_logic.guest_tickets_available()

    if models.Waiting.query.count() > 0 or (
            guest_tickets_available <
            login.current_user.purchase_group.total_guest_tickets_requested
    ):
        flask.flash(
            (
                'No tickets are available for your group.'
            ),
            'info'
        )

        if purchase_logic.wait_available(login.current_user):
            flask.flash(
                (
                    'If you and your group members still want to try to obtain '
                    'tickets, you should all join the waiting list.'
                ),
                'info'
            )
            return flask.redirect(flask.url_for('purchase.wait'))
        else:
            return flask.redirect(flask.url_for('dashboard.dashboard_home'))

    if flask.request.method != 'POST':
        return flask.render_template('group_purchase/checkout.html')

    tickets = [
        models.Ticket(
            request.requester,
            request.ticket_type.slug,
            request.ticket_type.price
        )
        for request in login.current_user.purchase_group.requests
        for _ in xrange(request.number_requested)
    ]

    DB.session.add_all(tickets)

    login.current_user.purchase_group.purchased = True

    DB.session.commit()

    APP.log_manager.log_event(
        'Completed Group Purchase',
        user=login.current_user,
        tickets=tickets,
        purchase_group=login.current_user.purchase_group
    )

    expiry_time = util.format_timedelta(APP.config['TICKET_EXPIRY_TIME'])

    for user in set(
            request.requester
            for request in login.current_user.purchase_group.requests
            if request.requester != login.current_user
    ):
        APP.email_manager.send_template(
            user.email,
            'Group Purchase Completed - Complete Payment Now!',
            'group_purchase_completed.email',
            name=user.forenames,
            group_leader=login.current_user.full_name,
            url=flask.url_for('purchase.complete_payment', _external=True),
            expiry_time=expiry_time
        )

    flask.flash('The tickets for your group have been reserved', 'success')
    flask.flash('You can now proceed to pay for your own tickets.', 'info')
    flask.flash(
        (
            'Your group members have been emailed to remind them to pay for '
            'their tickets.'
        ),
        'info'
    )
    flask.flash(
        'Any tickets not paid for within {0} will be cancelled.'.format(
            expiry_time
        ),
        'warning'
    )

    return flask.redirect(flask.url_for('purchase.complete_payment'))

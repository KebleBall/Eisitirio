# coding: utf-8
"""Views related to administrative tasks performed on users."""

from __future__ import unicode_literals

from flask.ext.login import current_user, login_user
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import login_manager
from eisitirio.helpers import util
from eisitirio.logic import affiliation_logic
from eisitirio.logic import purchase_logic

APP = app.APP
DB = db.DB

ADMIN_USERS = flask.Blueprint('admin_users', __name__)

@ADMIN_USERS.route('/admin/user/<int:user_id>/view')
@ADMIN_USERS.route(
    '/admin/user/<int:user_id>/view/page/selfactions/<int:self_actions_page>'
)
@ADMIN_USERS.route(
    '/admin/user/<int:user_id>/view/page/actions/<int:actions_page>'
)
@ADMIN_USERS.route(
    '/admin/user/<int:user_id>/view/page/events/<int:events_page>'
)
@login_manager.admin_required
def view_user(user_id, self_actions_page=1, actions_page=1, events_page=1):
    """Display a user's information."""
    user = models.User.get_by_id(user_id)

    if user:
        self_actions = user.actions.filter(
            models.Log.actor_id == models.Log.user_id
        ).order_by(
            models.Log.timestamp.desc()
        ).paginate(
            self_actions_page,
            10,
            True
        )

        other_actions = user.actions.filter(
            models.Log.actor_id != models.Log.user_id
        ).order_by(
            models.Log.timestamp.desc()
        ).paginate(
            actions_page,
            10,
            True
        )

        events = user.events.filter(
            models.Log.actor_id != models.Log.user_id
        ).order_by(
            models.Log.timestamp.desc()
        ).paginate(
            events_page,
            10,
            True
        )
    else:
        self_actions = None
        other_actions = None
        events = None

    return flask.render_template(
        'admin_users/view_user.html',
        user=user,
        self_actions=self_actions,
        other_actions=other_actions,
        events=events,
        self_actions_page=self_actions_page,
        actions_page=actions_page,
        events_page=events_page
    )

@ADMIN_USERS.route('/admin/user/<int:user_id>/impersonate')
@login_manager.admin_required
def impersonate_user(user_id):
    """Start impersonating a user.

    Some tasks are easier to do just by impersonating the user. This method
    logs in as the user to be impersonated, and sets a value in the session
    noting that it is an administrator performing these actions (used for
    logging)
        """
    user = models.User.get_by_id(user_id)

    if user:
        flask.session['actor_id'] = current_user.object_id

        login_user(
            user,
            remember=False
        )

        APP.log_manager.log_event(
            'Started impersonating user',
            [],
            user
        )

        return flask.redirect(flask.url_for('dashboard.dashboard_home'))
    else:
        flask.flash(
            'Could not find user, could not impersonate.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_USERS.route('/admin/user/<int:user_id>/give', methods=['GET', 'POST'])
@login_manager.admin_required
def give_user(user_id):
    """Give the user some tickets.

    Overrides the ticket limit.
    """
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

    user = models.User.get_by_id(user_id)

    if user:
        try:
            ticket_type = APP.config['TICKET_TYPES_BY_SLUG'][
                flask.request.form['give_ticket_type']
            ]
        except KeyError:
            flask.flash("Invalid/no ticket type selected", "error")
            return flask.redirect(flask.request.referrer or
                                  flask.url_for('admin.admin_home'))

        if (
            (
                'give_price_pounds' not in flask.request.form or
                flask.request.form['give_price_pounds'] == ''
            ) and (
                'give_price_pence' not in flask.request.form or
                flask.request.form['give_price_pence'] == ''
            )
        ):
            price = ticket_type.price
        else:
            price = util.parse_pounds_pence(flask.request.form,
                                            'give_price_pounds',
                                            'give_price_pence')

        num_tickets = int(flask.request.form['give_num_tickets'])

        if (
                'give_reason' not in flask.request.form or
                flask.request.form['give_reason'] == ''
        ):
            note = 'Given by {0} (#{1}) for no reason.'.format(
                current_user.full_name,
                current_user.object_id
            )
        else:
            note = 'Given by {0} (#{1}) with reason: {2}.'.format(
                current_user.full_name,
                current_user.object_id,
                flask.request.form['give_reason']
            )

        tickets = [
            models.Ticket(user, ticket_type.slug, price)
            for _ in xrange(num_tickets)
        ]

        for ticket in tickets:
            ticket.add_note(note)

        DB.session.add_all(tickets)
        DB.session.commit()

        APP.log_manager.log_event(
            'Gave {0} tickets'.format(
                num_tickets
            ),
            tickets,
            user
        )

        flask.flash(
            'Gave {0} {1} tickets'.format(
                user.forenames,
                num_tickets
            ),
            'success'
        )

        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_users.view_user',
                                            user_id=user.object_id))
    else:
        flask.flash(
            'Could not find user, could not give tickets.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_USERS.route('/admin/user/<int:user_id>/note', methods=['GET', 'POST'])
@login_manager.admin_required
def note_user(user_id):
    """Set the notes field for a user."""
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

    user = models.User.get_by_id(user_id)

    if user:
        user.note = flask.request.form['notes']
        DB.session.commit()

        APP.log_manager.log_event(
            'Updated notes',
            [],
            user
        )

        flask.flash(
            'Notes set successfully.',
            'success'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_users.view_user',
                                            user_id=user.object_id))
    else:
        flask.flash(
            'Could not find user, could not set notes.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_USERS.route('/admin/user/<int:user_id>/verify')
@login_manager.admin_required
def verify_user(user_id):
    """Manually mark a user as verified.

    If a user suffers an ID.10.T error and is unable to verify their email
    themselves, we can do it as adminstrators to save the hassle of walking the
    user through the process.
    """
    user = models.User.get_by_id(user_id)

    if user:
        user.verified = True
        DB.session.commit()

        APP.log_manager.log_event(
            'Verified email',
            [],
            user
        )

        flask.flash(
            'User marked as verified.',
            'success'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_users.view_user',
                                            user_id=user.object_id))
    else:
        flask.flash(
            'Could not find user, could not verify.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_USERS.route('/admin/user/<int:user_id>/demote')
@login_manager.admin_required
def demote_user(user_id):
    """Make an admin not an admin."""
    user = models.User.get_by_id(user_id)

    if user:
        user.demote()
        DB.session.commit()

        APP.log_manager.log_event(
            'Demoted user',
            [],
            user
        )

        flask.flash(
            'User demoted.',
            'success'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_users.view_user',
                                            user_id=user.object_id))
    else:
        flask.flash(
            'Could not find user, could not demote.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_USERS.route('/admin/user/<int:user_id>/promote')
@login_manager.admin_required
def promote_user(user_id):
    """Make a user an administrator."""
    user = models.User.get_by_id(user_id)

    if user:
        user.promote()
        DB.session.commit()

        APP.log_manager.log_event(
            'Promoted user',
            [],
            user
        )

        flask.flash(
            'User promoted.',
            'success'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_users.view_user',
                                            user_id=user.object_id))
    else:
        flask.flash(
            'Could not find user, could not promote.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_USERS.route('/admin/user/<int:user_id>/add_manual_battels')
@login_manager.admin_required
def add_manual_battels(user_id):
    """Set up a battels account for a user.

    If a user wasn't automatically matched to a battels account (common for
    staff members as the college rarely provides anything but the list of
    undergraduates), we can manually create a battels account tied to the user's
    email address.
    """
    user = models.User.get_by_id(user_id)

    if user:
        user.add_manual_battels()

        APP.log_manager.log_event(
            'Manually set up battels',
            [],
            user
        )

        flask.flash(
            'Battels set up for user.',
            'success'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin_users.view_user',
                                            user_id=user.object_id))
    else:
        flask.flash(
            'Could not find user, could not manually set up battels.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

@ADMIN_USERS.route('/admin/user/<int:user_id>/verify_affiliation')
@login_manager.admin_required
def verify_affiliation(user_id):
    """Mark a user's affiliation as being verified.

    In limited release, users' affiliations must be varified to ensure only
    current college members and graduands are able to purchase tickets.
    """
    user = models.User.get_by_id(user_id)

    if user:
        affiliation_logic.verify_affiliation(user)

        APP.log_manager.log_event(
            'Verified affiliation',
            [],
            user
        )

    return flask.redirect(flask.url_for('admin_users.verify_affiliations'))

@ADMIN_USERS.route('/admin/user/<int:user_id>/deny_affiliation')
@login_manager.admin_required
def deny_affiliation(user_id):
    """Mark a user's affiliation as incorrect/invalid."""
    user = models.User.get_by_id(user_id)

    if user:
        affiliation_logic.deny_affiliation(user)

        APP.log_manager.log_event(
            'Denied affiliation',
            [],
            user
        )

    return flask.redirect(flask.url_for('admin_users.verify_affiliations'))

@ADMIN_USERS.route('/admin/verify_affiliations')
@login_manager.admin_required
def verify_affiliations():
    """Allow an admin to verify many users' affiliations.

    Presents a list of users who have registered but need their affiliation
    verifying with buttons for each to verify/deny the affiliation.
    """
    return flask.render_template('admin_users/verify_affiliations.html',
                                 users=affiliation_logic.get_unverified_users())

@ADMIN_USERS.route('/admin/user/<int:user_id>/collect', methods=['GET', 'POST'])
@login_manager.admin_required
def collect_tickets(user_id):
    """Display an interface to collect tickets.

    Tickets are attached to barcoded wristbands upon collection. This presents
    an interface displaying all the users tickets, with a field for adding the
    barcode to each (intended to be filled using a barcode scanner).
    """
    user = models.User.get_by_id(user_id)

    if user:
        return flask.render_template(
            'admin_users/collect_tickets.html',
            user=user
        )
    else:
        flask.flash(
            'Could not find user, could not process ticket collection.',
            'warning'
        )
        return flask.redirect(flask.request.referrer or
                              flask.url_for('admin.admin_home'))

